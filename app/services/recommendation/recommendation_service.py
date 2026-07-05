from typing import Any

from app.services.recommendation.eligibility_rules import PolicyEligibilityEngine
from app.services.recommendation.policy_loader import PolicyLoaderService


class RecommendationService:
    """
    정책 데이터를 로드하고 PolicyEligibilityEngine으로 각 정책을 판정해
    맞춤형 정책 추천 결과(YES/NO + 사유)를 만듭니다.
    """

    def __init__(self, policy_loader: PolicyLoaderService, eligibility_engine: PolicyEligibilityEngine):
        self.policy_loader = policy_loader
        self.eligibility_engine = eligibility_engine

    def recommend_svc(self, user_profile: dict) -> dict[str, Any]:
        policies = self.policy_loader.get_policies()
        result = self._recommend_policies(user_profile, policies)
        return self._to_policy_id_result(result, policies)

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

        return {
            "available_policy_ids": available_ids,
            "unavailable_policy_ids": unavailable_ids,

            "available_policies": available_policies,
            "unavailable_policies": unavailable_policies,

            "fail_reasons_by_policy_id": fail_reasons,
        }

    @staticmethod
    def _to_policy_id_result(result: dict[str, Any], policies: list[dict]) -> dict[str, Any]:
        """rule engine 결과의 plcyNo 기반 식별자를 backend DB의 policy_id로 변환합니다."""
        plcy_no_to_policy_id = {str(p.get("plcyNo")): p.get("policy_id") for p in policies}

        def to_policy_id(plcy_no):
            return plcy_no_to_policy_id.get(str(plcy_no), plcy_no)

        for policy_result in result.get("available_policies", []) + result.get("unavailable_policies", []):
            policy_result["policy_id"] = to_policy_id(policy_result.get("policy_id"))

        result["available_policy_ids"] = [to_policy_id(pn) for pn in result.get("available_policy_ids", [])]
        result["unavailable_policy_ids"] = [to_policy_id(pn) for pn in result.get("unavailable_policy_ids", [])]
        result["fail_reasons_by_policy_id"] = {
            str(to_policy_id(pn)): reasons
            for pn, reasons in result.get("fail_reasons_by_policy_id", {}).items()
        }
        return result
