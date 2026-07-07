from typing import Any

from app.services.recommendation.eligibility_rules import PolicyEligibilityEngine
from app.services.recommendation.policy_loader import PolicyLoaderService
from app.services.recommendation.similarity_search import PolicySimilarityService

# 신청기간 실패 사유에 따라 "신청 마감"과 "신청기간 종료" 탭을 구분합니다.
CLOSED_STATUSES = {"CLOSED_CODE"}
EXPIRED_STATUSES = {"NOT_STARTED", "ENDED"}

POLICY_BUCKET_KEYS = ("available_policies", "closed_policies", "expired_policies", "unavailable_policies")


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

    def recommend_chat_svc(self, user_profile: dict, chat: str, top_k: int = 5) -> dict[str, Any]:
        policies = self.policy_loader.get_policies()
        result = self._recommend_policies(user_profile, policies)

        fail_reasons_by_plcyno = result["fail_reasons_by_plcyNo"]
        top_results: dict[str, Any] = {}

        for bucket in POLICY_BUCKET_KEYS:
            top_matches = self.similarity_service.search(chat, result[bucket], top_k=top_k)
            if bucket != "available_policies":
                for match in top_matches:
                    details = fail_reasons_by_plcyno.get(str(match.get("plcyNo")), {})
                    match["fail_reasons"] = [
                        {"check": check, "reason": detail["reason"]}
                        for check, detail in details.items()
                        if not detail.get("match")
                    ]
            top_results[bucket] = top_matches

        return top_results

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
