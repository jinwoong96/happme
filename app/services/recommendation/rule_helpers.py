def make_result(match: bool, reason: str, user_value=None, policy_value=None) -> dict:
    return {
        "match": match,
        "reason": reason,
        "user_value": user_value,
        "policy_value": policy_value,
    }


def is_empty_or_unlimited(value) -> bool:
    if value is None:
        return True
    return str(value).strip() in ["", "제한없음", "제한 없음", "무관", "0"]
