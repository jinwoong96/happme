from typing import Any

from app.services.recommendation.eligibility_rules import PolicyEligibilityEngine
from app.services.recommendation.policy_loader import PolicyLoaderService
from app.services.recommendation.similarity_search import PolicySimilarityService

# 신청기간 실패 사유에 따라 내부적으로는 "신청 마감"/"신청기간 종료"를 구분해 판정하지만,
# 화면에는 굳이 나눌 필요가 없는 비슷한 내용이라 recommend_chat_svc의 최종 응답에서는 하나로 합친다.
CLOSED_STATUSES = {"CLOSED_CODE"}
EXPIRED_STATUSES = {"NOT_STARTED", "ENDED"}

POLICY_BUCKET_KEYS = ("available_policies", "closed_policies", "expired_policies", "unavailable_policies")

# 조건 불만족 사유를 끝까지 계산해줄 가치가 있으려면(화면에 보여줄 게 있으려면) 애초에 판정
# 대상 자체가 적어야 한다. 이보다 많으면(보통 전체 카탈로그 수천 건) rule engine이 실패 사유를
# 다 채우지 않고 첫 실패 검사에서 바로 다음 정책으로 넘어간다(eligibility_rules.py의 full_detail).
FULL_DETAIL_MAX_POLICIES = 20

# region 체크의 policy_value.type(region_matcher.py) -> 화면에 보여줄 지역 규모 탭 키.
REGION_SCOPE_TO_BUCKET = {
    "광역": "wide_policies",
    "시도범위": "province_policies",
    "시군구범위": "local_policies",
}

# 정책 데이터의 lclsfNm(대분류)이 두 세대 taxonomy가 섞여 있어("교육" vs "교육･직업훈련" 등)
# 정규화한다. BOKJIRO(지자체/중앙부처)는 lclsfNm이 전부 "복지" 고정값이라 세부 카테고리
# 정보가 없고, 대신 mclsfNm에 복지로의 "관심주제" 값이 그대로 들어있다.
LCLSF_ALIASES = {
    "일자리": "일자리",
    "주거": "주거",
    "교육": "교육",
    "교육･직업훈련": "교육",
    "참여권리": "참여권리",
    "참여･기반": "참여권리",
}

# 이 lclsfNm 값들은 "복지문화" 계열로 뭉뚱그려져 있어(ONTONG 구세대 이름 포함, BOKJIRO 고정값
# 포함) 그 자체로는 카테고리를 못 정하고 mclsfNm(중분류/관심주제)을 봐야 한다.
WELFARE_FAMILY_LCLSF = {"복지문화", "금융･복지･문화", "복지"}

# mclsfNm(ONTONG 중분류 또는 BOKJIRO 관심주제) -> 세분화된 카테고리.
# "복지문화" 하나로 묶으면 ONTONG+BOKJIRO 합쳐 전체의 절반 가까이가 쏠려서 의미가 없어져,
# 성격이 다른 금융지원/건강·돌봄/문화예술 3개로 쪼갰다.
MCLSF_TO_CATEGORY = {
    "취약계층 및 금융지원": "복지·금융", "서민금융": "복지·금융",
    "건강": "건강·돌봄", "신체건강": "건강·돌봄", "정신건강": "건강·돌봄",
    "생활지원": "건강·돌봄", "안전·위기": "건강·돌봄", "임신·출산": "건강·돌봄",
    "입양·위탁": "건강·돌봄", "보호·돌봄": "건강·돌봄",
    "문화활동": "문화·예술", "문화활동 및 생활지원": "문화·예술",
    "예술인지원": "문화·예술", "문화·여가": "문화·예술",
    "일자리": "일자리", "주거": "주거", "교육": "교육", "보육": "교육",
    "법률": "참여권리", "기타": "기타",
}

# 정책명에 이 키워드가 있으면 해당 카테고리로 우선 배정한다. 정책 하나에 관심주제/대분류가
# 여러 개 나열된 경우(BOKJIRO 원본 기준 지자체 29.6%, 중앙부처 49.1%가 이런 다중값이었음),
# 그냥 배열의 첫 번째 값을 쓰면 실제 내용과 안 맞는 경우가 꽤 있었다(예: "학자금대출 이자지원"이
# 관심주제 "일자리,교육" 순서라 "일자리"로 잘못 분류됨). 정책명과 매칭되는 키워드가 있는 첫
# 번째 태그를 대표로 쓰고, 아무 것도 안 맞으면 원래 순서상 첫 번째로 폴백한다.
KEYWORD_HINTS = {
    "복지·금융": ["대출", "이자", "금융", "적금", "저축"],
    "건강·돌봄": ["의료", "건강", "진료", "치료", "돌봄", "임신", "출산", "난임", "산모", "산후", "입양", "위탁"],
    "문화·예술": ["문화", "예술", "공연", "전시", "여가"],
    "교육": ["학자금", "교육", "장학", "학비", "학습"],
    "주거": ["주거", "주택", "전세", "임대", "월세", "기숙사"],
    "일자리": ["취업", "창업", "일자리", "채용", "구직"],
    "참여권리": ["참여", "권익", "법률"],
}


def _normalize_category(policy: dict) -> str:
    """policy_result 딕셔너리(lclsfNm/mclsfNm/policy_name 포함)를 보고 화면에 보여줄 최종
    카테고리 하나를 정한다. DB의 lclsfNm/mclsfNm은 원본 그대로(콤마로 여러 값 포함 가능)
    보존돼 있으므로, 여기서 후보들을 뽑아 정책명과 키워드가 맞는 걸 대표로 선택한다."""
    lclsf_tags = [t.strip() for t in str(policy.get("lclsfNm") or "").split(",") if t.strip()]
    mclsf_tags = [t.strip() for t in str(policy.get("mclsfNm") or "").split(",") if t.strip()]
    lclsf_first = lclsf_tags[0] if lclsf_tags else ""

    if lclsf_first in WELFARE_FAMILY_LCLSF:
        candidates = [MCLSF_TO_CATEGORY.get(t, "기타") for t in mclsf_tags] or ["기타"]
    else:
        candidates = [LCLSF_ALIASES.get(t, "기타") for t in lclsf_tags] or ["기타"]

    name = str(policy.get("policy_name") or "")
    for category in candidates:
        if any(hint in name for hint in KEYWORD_HINTS.get(category, [])):
            return category
    return candidates[0]


class RecommendationService:
    """
    정책 데이터를 로드하고 PolicyEligibilityEngine으로 각 정책을 판정합니다. 내부적으로는
    지금도 4개 카테고리(조건만족/신청마감/기간종료/조건불만족)로 분류하지만, 화면에는 조건을
    만족한 정책만 노출합니다(마감/종료/불만족 정책을 보여줄 필요는 없다고 판단). 신청기간이
    유효하지 않은 정책을 걸러내는 데는 여전히 이 분류가 쓰입니다.
    채팅 기반 추천(recommend_chat_svc)은 조건 만족 정책을 다시 지역 규모(전국급/시도범위/
    시군구범위)로 나눠서 반환합니다.
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
        각 정책에 정규화된 category를 붙인다. 마감/종료/조건불만족 정책은 화면에 보여줄 필요가
        없어 아예 응답에서 뺀다. 대신 조건 만족 정책을 지역 규모(전국급/시도범위/시군구범위)
        3개로 나눠서 반환한다.
        chat이 빈 문자열이면 유사도 계산 없이 rule engine이 판정한 순서를 그대로 반환한다.
        """
        policies = self.policy_loader.get_policies()
        result = self._recommend_policies(user_profile, policies)

        available = result["available_policies"]
        category_by_plcyno = {
            str(p.get("plcyNo")): _normalize_category(p) for p in available
        }
        # similarity_service.search()는 policy_search_docs.json 기준이라 rgtrInstCdNm이 없으므로,
        # rule engine이 이미 만들어둔 available에서 plcyNo로 다시 채워준다.
        rgtr_inst_by_plcyno = {str(p.get("plcyNo")): p.get("rgtrInstCdNm") for p in available}
        region_scope_by_plcyno = {str(p.get("plcyNo")): p.get("region_scope") for p in available}

        if chat and chat.strip():
            matches = self.similarity_service.search(chat, available, top_k=None)
        else:
            # 채팅 텍스트가 없으면 유사도 계산을 생략하고 rule engine이 판정한 순서를 그대로 사용한다.
            # TODO: 추후 이 경우엔 유사도 대신 사용자 프로필 기반 우선순위로 대체 예정
            matches = [
                {
                    "plcyNo": p.get("plcyNo"),
                    "policy_name": p.get("policy_name"),
                    "policy_summary": p.get("policy_summary"),
                }
                for p in available
            ]

        buckets: dict[str, list] = {key: [] for key in REGION_SCOPE_TO_BUCKET.values()}
        for match in matches:
            plcyno_str = str(match.get("plcyNo"))
            match["category"] = category_by_plcyno.get(plcyno_str, "기타")
            match.setdefault("rgtrInstCdNm", rgtr_inst_by_plcyno.get(plcyno_str))
            scope = region_scope_by_plcyno.get(plcyno_str)
            bucket_key = REGION_SCOPE_TO_BUCKET.get(scope, "local_policies")
            buckets[bucket_key].append(match)

        return buckets

    def _recommend_policies(self, user: dict, policies: list[dict]) -> dict[str, Any]:
        buckets: dict[str, list] = {key: [] for key in POLICY_BUCKET_KEYS}
        plcyno_buckets: dict[str, list] = {key: [] for key in POLICY_BUCKET_KEYS}

        fail_reasons = {}

        # 대상이 많을 때(보통 전체 카탈로그 수천 건)는 화면에 불만족 사유를 보여줄 일이 없으니
        # rule engine이 첫 실패 검사에서 바로 다음 정책으로 넘어가도록 해서 시간을 아낀다.
        full_detail = len(policies) <= FULL_DETAIL_MAX_POLICIES

        for policy in policies:
            match_result = self.eligibility_engine.evaluate(user, policy, full_detail=full_detail)
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
                # 조건을 만족한 정책만 이 값이 채워진다(region 체크까지 도달한 경우에만).
                # 화면에서 전국급/시도범위/시군구범위 탭으로 나누는 데 쓰인다.
                "region_scope": (match_result["details"].get("region") or {}).get("policy_value", {}).get("type"),
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
