from typing import Any

from app.services.recommendation.eligibility_rules import PolicyEligibilityEngine
from app.services.recommendation.policy_loader import PolicyLoaderService
from app.services.recommendation.similarity_search import PolicySimilarityService

# 신청기간 실패 사유에 따라 내부적으로는 "신청 마감"/"신청기간 종료"를 구분해 판정하지만,
# 화면에는 굳이 나눌 필요가 없는 비슷한 내용이라 recommend_chat_svc의 최종 응답에서는 하나로 합친다.
CLOSED_STATUSES = {"CLOSED_CODE"}
EXPIRED_STATUSES = {"NOT_STARTED", "ENDED"}

POLICY_BUCKET_KEYS = ("available_policies", "closed_policies", "expired_policies", "unavailable_policies")

# 정책 데이터의 lclsfNm(대분류)이 두 세대 taxonomy가 섞여 있고("교육" vs "교육･직업훈련" 등),
# 콤마로 여러 값이 붙은 행도 있어("일자리,교육") 화면에 보여줄 카테고리 5종으로 정규화한다.
CATEGORY_ALIASES = {
    "일자리": "일자리",
    "주거": "주거",
    "교육": "교육",
    "교육･직업훈련": "교육",
    "복지문화": "복지문화",
    "금융･복지･문화": "복지문화",
    "참여권리": "참여권리",
    "참여･기반": "참여권리",
}


def _normalize_category(raw_category) -> str:
    first_value = str(raw_category or "").split(",")[0].strip()
    return CATEGORY_ALIASES.get(first_value, "기타")


class RecommendationService:
    """
    정책 데이터를 로드하고 PolicyEligibilityEngine으로 각 정책을 판정해
    맞춤형 정책 추천 결과를 4개 카테고리로 만듭니다.
    - available_policies:   조건 만족
    - closed_policies:      신청 마감(원본 API가 마감 코드로 명시)
    - expired_policies:     신청기간 종료(신청 시작 전/종료 등 날짜 계산으로 판단)
    - unavailable_policies: 신청기간은 유효하지만 다른 조건 불만족
    채팅 기반 추천은 4개 카테고리 각각에서 PolicySimilarityService로 유사도 top_k를 뽑습니다.
    정책 식별자는 plcyNo을 사용합니다. policy_id(backend DB PK)는 backend에서 plcyNo으로 조회해 붙입니다.
    """

    def __init__(
        self,
        policy_loader: PolicyLoaderService,
        eligibility_engine: PolicyEligibilityEngine,
        similarity_service: PolicySimilarityService,
    ):
        self.policy_loader = policy_loader
        self.eligibility_engine = eligibility_engine
        self.similarity_service = similarity_service

    def recommend_svc(self, user_profile: dict) -> dict[str, Any]:
        policies = self.policy_loader.get_policies()
        return self._recommend_policies(user_profile, policies)

    def recommend_chat_svc(self, user_profile: dict, chat: str) -> dict[str, Any]:
        """
        top_k 제한 없이(top_k=None) 조건을 통과한 정책을 전부 유사도 순으로 반환하고,
        각 정책에 정규화된 category를 붙인다. "신청 마감"/"신청기간 종료"는 비슷한 내용이라
        화면에서는 하나의 closed_or_expired_policies로 합쳐서 내려준다.
        chat이 빈 문자열이면 유사도 계산 없이 rule engine이 판정한 순서를 그대로 반환한다.
        """
        policies = self.policy_loader.get_policies()
        result = self._recommend_policies(user_profile, policies)

        fail_reasons_by_plcyno = result["fail_reasons_by_plcyNo"]
        category_by_plcyno = {
            str(p.get("plcyNo")): _normalize_category(p.get("large_category"))
            for bucket in POLICY_BUCKET_KEYS
            for p in result[bucket]
        }

        def build_bucket(policies_in_bucket: list[dict], with_fail_reasons: bool) -> list[dict]:
            # similarity_service.search()는 policy_search_docs.json 기준이라 rgtrInstCdNm이 없으므로,
            # rule engine이 이미 만들어둔 policies_in_bucket에서 plcyNo로 다시 채워준다.
            rgtr_inst_by_plcyno = {str(p.get("plcyNo")): p.get("rgtrInstCdNm") for p in policies_in_bucket}

            if chat and chat.strip():
                matches = self.similarity_service.search(chat, policies_in_bucket, top_k=None)
            else:
                # 채팅 텍스트가 없으면 유사도 계산을 생략하고 rule engine이 판정한 순서를 그대로 사용한다.
                # TODO: 추후 이 경우엔 유사도 대신 사용자 프로필 기반 우선순위로 대체 예정
                matches = [
                    {
                        "plcyNo": p.get("plcyNo"),
                        "policy_name": p.get("policy_name"),
                        "policy_summary": p.get("policy_summary"),
                    }
                    for p in policies_in_bucket
                ]
            for match in matches:
                match["category"] = category_by_plcyno.get(str(match.get("plcyNo")), "기타")
                match.setdefault("rgtrInstCdNm", rgtr_inst_by_plcyno.get(str(match.get("plcyNo"))))
                if with_fail_reasons:
                    details = fail_reasons_by_plcyno.get(str(match.get("plcyNo")), {})
                    match["fail_reasons"] = [
                        {"check": check, "reason": detail["reason"]}
                        for check, detail in details.items()
                        if not detail.get("match")
                    ]
            return matches

        return {
            "available_policies": build_bucket(result["available_policies"], False),
            "closed_or_expired_policies": build_bucket(
                result["closed_policies"] + result["expired_policies"], True
            ),
            "unavailable_policies": build_bucket(result["unavailable_policies"], True),
        }

    def _recommend_policies(self, user: dict, policies: list[dict]) -> dict[str, Any]:
        buckets: dict[str, list] = {key: [] for key in POLICY_BUCKET_KEYS}
        plcyno_buckets: dict[str, list] = {key: [] for key in POLICY_BUCKET_KEYS}

        fail_reasons = {}

        for policy in policies:
            match_result = self.eligibility_engine.evaluate(user, policy)
            plcy_no = policy.get("plcyNo")

            policy_result = {
                "plcyNo": plcy_no,
                "policy_name": policy.get("plcyNm"),
                "policy_summary": policy.get("plcyExplnCn"),

                # 등록기관명. 같은 이름의 정책이 지자체별로 여러 개 등록돼 있는 경우가 많아서
                # (예: "전세보증금반환보증 보증료 지원"이 세종/광주/부산 등 기관마다 따로 있음)
                # 화면에서 어느 기관/지역 정책인지 구분할 수 있도록 같이 내려준다.
                "rgtrInstCdNm": policy.get("rgtrInstCdNm"),

                "large_category": policy.get("lclsfNm", "기타"),
                "middle_category": policy.get("mclsfNm", "기타"),

                # 유사도 계산용 필드 추가
                "lclsfNm": policy.get("lclsfNm", ""),
                "mclsfNm": policy.get("mclsfNm", ""),
                "plcyKywdNm": policy.get("plcyKywdNm", ""),
                "plcyExplnCn": policy.get("plcyExplnCn", ""),
                "plcySprtCn": policy.get("plcySprtCn", ""),

                "result": match_result["result"],
                "details": match_result["details"],
            }

            bucket = self._bucket_for(match_result)
            buckets[bucket].append(policy_result)
            plcyno_buckets[bucket].append(plcy_no)

            if bucket != "available_policies":
                fail_reasons[str(plcy_no)] = match_result["details"]

        print(
            f"[RecommendationService] 조건만족 {len(buckets['available_policies'])} / "
            f"신청마감 {len(buckets['closed_policies'])} / "
            f"기간종료 {len(buckets['expired_policies'])} / "
            f"조건불만족 {len(buckets['unavailable_policies'])} (전체 {len(policies)})"
        )

        return {
            "available_plcyNos": plcyno_buckets["available_policies"],
            "closed_plcyNos": plcyno_buckets["closed_policies"],
            "expired_plcyNos": plcyno_buckets["expired_policies"],
            "unavailable_plcyNos": plcyno_buckets["unavailable_policies"],

            "available_policies": buckets["available_policies"],
            "closed_policies": buckets["closed_policies"],
            "expired_policies": buckets["expired_policies"],
            "unavailable_policies": buckets["unavailable_policies"],

            "fail_reasons_by_plcyNo": fail_reasons,
        }

    @staticmethod
    def _bucket_for(match_result: dict[str, Any]) -> str:
        apply_period = match_result["details"]["apply_period"]

        if not apply_period["match"]:
            status = (apply_period.get("policy_value") or {}).get("status")
            if status in CLOSED_STATUSES:
                return "closed_policies"
            return "expired_policies"

        if match_result["result"] == "YES":
            return "available_policies"

        return "unavailable_policies"
