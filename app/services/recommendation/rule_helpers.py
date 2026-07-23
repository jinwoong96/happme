def make_result(match: bool, reason: str, user_value=None, policy_value=None) -> dict:
    """eligibility_rules.py의 각 조건 검사 함수가 공통으로 쓰는 결과 형식을 만든다."""
    return {
        "match": match,
        "reason": reason,
        "user_value": user_value,
        "policy_value": policy_value,
    }


def is_empty_or_unlimited(value) -> bool:
    """정책 조건 값이 비어있거나 "제한없음"/"무관"처럼 사실상 제한이 없는 값인지 확인한다."""
    if value is None:
        return True
    return str(value).strip() in ["", "제한없음", "제한 없음", "무관", "0"]
