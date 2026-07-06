from typing import Any

from app.services.recommendation.eligibility_rules import PolicyEligibilityEngine
from app.services.recommendation.policy_loader import PolicyLoaderService
from app.services.recommendation.similarity_search import PolicySimilarityService


class RecommendationService:
    """
    정책 데이터를 로드하고 PolicyEligibilityEngine으로 각 정책을 판정해
    맞춤형 정책 추천 결과(YES/NO + 사유)를 만듭니다.
    채팅 기반 추천은 rule engine 통과 정책들 중 PolicySimilarityService로 유사도 top_k를 뽑습니다.
    policy_id는 plcyNo을 그대로 사용합니다(같은 값, 키 이름만 다름).
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

        available_top = self.similarity_service.search(chat, result["available_policies"], top_k=top_k)
        unavailable_top = self.similarity_service.search(chat, result["unavailable_policies"], top_k=top_k)

        fail_reasons_by_policy_id = result["fail_reasons_by_policy_id"]
        for match in unavailable_top:
            details = fail_reasons_by_policy_id.get(str(match.get("policy_id")), {})
            match["fail_reasons"] = [
                {"check": check, "reason": detail["reason"]}
                for check, detail in details.items()
                if not detail.get("match")
            ]

        return {
            "available_policies": available_top,
            "unavailable_policies": unavailable_top,
        }

    def _recommend_policies(self, user: dict, policies: list[dict]) -> dict[str, Any]:
        available_policies = []
        unavailable_policies = []

        available_ids = []
        unavailable_ids = []

        fail_reasons = {}

        for policy in policies:
            match_result = self.eligibility_engine.evaluate(user, policy)

            policy_result = {
                "policy_id": policy.get("plcyNo"),
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

            if match_result.get("result") == "YES":
                available_policies.append(policy_result)
                available_ids.append(policy.get("plcyNo"))
            else:
                unavailable_policies.append(policy_result)
                unavailable_ids.append(policy.get("plcyNo"))

                fail_reasons[str(policy.get("plcyNo"))] = match_result["details"]

        print(f"[RecommendationService] rule engine 통과 정책 수: {len(available_policies)} / {len(policies)}")

        return {
            "available_policy_ids": available_ids,
            "unavailable_policy_ids": unavailable_ids,

            "available_policies": available_policies,
            "unavailable_policies": unavailable_policies,

            "fail_reasons_by_policy_id": fail_reasons,
        }
