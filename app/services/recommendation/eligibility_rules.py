import re
from datetime import datetime

from app.services.recommendation.code_mapping import JOB_MAP, MAJOR_MAP, MARRIAGE_MAP, SBIZ_MAP, SCHOOL_MAP
from app.services.recommendation.region_matcher import RegionMatcher
from app.services.recommendation.rule_helpers import is_empty_or_unlimited, make_result

SBIZ_USER_CHECK = {
    "중소기업": lambda u: u.get("company_type") == "중소기업",
    "여성": lambda u: u.get("gender") == "여",
    "기초생활수급자": lambda u: u.get("basic_livelihood") is True,
    "한부모가정": lambda u: u.get("single_parent") is True,
    "장애인": lambda u: u.get("disability") is True,
    "농업인": lambda u: u.get("employment_status") == "영농종사자",
    "군인": lambda u: u.get("employment_status") == "군인",
}


class PolicyEligibilityEngine:
    """
    사용자 프로필과 정책 조건을 항목별(신청기간/나이/지역/혼인/학력/특수계층/취업상태)로
    대조해 신청 가능 여부(YES/NO)와 사유를 판단합니다.
    """

    def __init__(self, region_matcher: RegionMatcher):
        self.region_matcher = region_matcher

    # apply_period은 _bucket_for가, region은 지역 규모 탭 분류가 항상 필요로 하므로 순서상
    # 앞쪽에 둔다 - full_detail=False로 중간에 멈추더라도 이 둘은 이미 계산되어 있다.
    _CHECK_ORDER = ("apply_period", "age", "region", "marriage", "school_status", "major", "sbiz", "job")

    def evaluate(self, user: dict, policy: dict, full_detail: bool = True) -> dict:
        """
        full_detail=False면 조건 하나라도 불만족하는 순간 나머지 검사는 건너뛴다(조건 불만족
        사유를 상세히 보여줄 필요가 없을 때 - 예: 전체 정책 카탈로그처럼 대상이 많은 경우 -
        속도를 위해). full_detail=True면 지금까지처럼 8개 검사를 전부 실행해서 완전한 사유를
        남긴다(대상이 15~20개 이하로 적어서 왜 불만족인지가 실제로 보여질 수 있는 경우).
        """
        checkers = {
            "apply_period": lambda: self._match_apply_period(user, policy),
            "age": lambda: self._match_age(user, policy),
            "region": lambda: self.region_matcher.match(user, policy),
            "marriage": lambda: self._match_marriage(user, policy),
            "school_status": lambda: self._match_school_status(user, policy),
            "major": lambda: self._match_major(user, policy),
            "sbiz": lambda: self._match_sbiz(user, policy),
            "job": lambda: self._match_job(user, policy),
        }

        checks = {}
        for key in self._CHECK_ORDER:
            checks[key] = checkers[key]()
            if not full_detail and not checks[key]["match"]:
                break

        is_matched = all(v["match"] for v in checks.values())

        return {
            "result": "YES" if is_matched else "NO",
            "details": checks,
        }

    @staticmethod
    def _parse_yyyymmdd(value):
        if value is None:
            return None

        value = str(value).strip()

        if not value or value in ["0", "제한없음", "상시"]:
            return None

        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except Exception:
            return None

    @classmethod
    def _parse_apply_period(cls, aply_ymd):
        """
        예:
        "20250301 ~ 20251231"
        "2025.03.01 ~ 2025.12.31"
        "2025-03-01 ~ 2025-12-31"
        """
        if not aply_ymd:
            return None, None

        text = str(aply_ymd).strip()

        dates = re.findall(r"\d{4}[.\-/]?\d{2}[.\-/]?\d{2}", text)

        if len(dates) < 2:
            return None, None

        start = re.sub(r"[.\-/]", "", dates[0])
        end = re.sub(r"[.\-/]", "", dates[1])

        return cls._parse_yyyymmdd(start), cls._parse_yyyymmdd(end)

    def _match_apply_period(self, user, policy):
        """
        aplyPrdSeCd:
        0057003 = 마감
        0057002 = 상시
        0057001 = 특정기간

        policy_value["status"]로 실패 사유를 구분합니다(추천 결과 탭 분류에 사용):
        - CLOSED_CODE: 원본 API가 명시적으로 마감 코드(0057003)를 준 경우
        - NOT_STARTED / ENDED: 날짜 계산으로 판단한 신청 전/신청기간 종료
        - OPEN / OPEN_ALWAYS / OPEN_UNKNOWN: 신청 가능(또는 판단 불가로 통과)
        """
        today = datetime.today().date()

        period_code = policy.get("aplyPrdSeCd")
        period_text = policy.get("aplyYmd")

        policy_value = {
            "aplyPrdSeCd": period_code,
            "aplyYmd": period_text,
            "today": str(today),
        }

        if period_code == "0057003":
            policy_value["status"] = "CLOSED_CODE"
            return make_result(False, "신청기간이 마감된 정책", str(today), policy_value)

        if period_code == "0057002":
            policy_value["status"] = "OPEN_ALWAYS"
            return make_result(True, "상시 신청 가능 정책", str(today), policy_value)

        start_date, end_date = self._parse_apply_period(period_text)

        if start_date and end_date:
            policy_value["start_date"] = str(start_date)
            policy_value["end_date"] = str(end_date)

            if today < start_date:
                policy_value["status"] = "NOT_STARTED"
                return make_result(
                    False,
                    f"신청 시작 전 정책입니다. 신청 시작일은 {start_date}입니다.",
                    str(today),
                    policy_value,
                )

            if today > end_date:
                policy_value["status"] = "ENDED"
                return make_result(
                    False,
                    f"신청기간이 종료된 정책입니다. 신청 종료일은 {end_date}입니다.",
                    str(today),
                    policy_value,
                )

            policy_value["status"] = "OPEN"
            return make_result(True, "현재 신청기간 내에 있는 정책", str(today), policy_value)

        if period_code == "0057001":
            policy_value["status"] = "OPEN_UNKNOWN"
            return make_result(
                True,
                "특정기간 정책이지만 신청기간 문자열을 해석하지 못해 통과",
                str(today),
                policy_value,
            )

        policy_value["status"] = "OPEN_UNKNOWN"
        return make_result(True, "신청기간 조건 판단 정보 없음", str(today), policy_value)

    @staticmethod
    def _match_age(user, policy):
        if policy.get("sprtTrgtAgeLmtYn") == "Y":
            return make_result(True, "연령 제한 없음")

        user_age = user.get("age")
        if user_age is None:
            return make_result(False, "사용자 나이 정보 없음")

        user_age = int(user_age)
        min_age = policy.get("sprtTrgtMinAge")
        max_age = policy.get("sprtTrgtMaxAge")

        policy_value = {"min": min_age, "max": max_age}

        if not is_empty_or_unlimited(min_age) and user_age < int(min_age):
            return make_result(False, f"{user_age}세로 최소 연령 {min_age}세 미만", user_age, policy_value)

        if not is_empty_or_unlimited(max_age) and user_age > int(max_age):
            return make_result(False, f"{user_age}세로 최대 연령 {max_age}세 초과", user_age, policy_value)

        return make_result(True, "연령 조건 충족", user_age, policy_value)

    @staticmethod
    def _match_marriage(user, policy):
        policy_marriage = policy.get("mrgSttsCd")

        if is_empty_or_unlimited(policy_marriage):
            return make_result(True, "혼인 제한 없음")

        allowed_value = MARRIAGE_MAP.get(policy_marriage)

        if is_empty_or_unlimited(allowed_value):
            return make_result(True, "혼인 제한 없음")

        user_value = user.get("marital_status")

        if user_value != allowed_value:
            return make_result(False, f"혼인상태가 정책 조건({allowed_value})과 다름", user_value, allowed_value)

        return make_result(True, "혼인 조건 충족", user_value, allowed_value)

    @staticmethod
    def _match_school_status(user, policy):
        policy_school = policy.get("schoolCd")

        if is_empty_or_unlimited(policy_school):
            return make_result(True, "학력 제한 없음")

        allowed_value = SCHOOL_MAP.get(policy_school)

        if is_empty_or_unlimited(allowed_value):
            return make_result(True, "학력 제한 없음")

        user_value = user.get("education")

        if user_value != allowed_value:
            return make_result(False, f"학력이 정책 조건({allowed_value})과 다름", user_value, allowed_value)

        return make_result(True, "학력 조건 충족", user_value, allowed_value)

    @staticmethod
    def _match_major(user, policy):
        policy_major = policy.get("plcyMajorCd")

        if is_empty_or_unlimited(policy_major):
            return make_result(True, "전공계열 제한 없음")

        allowed_value = MAJOR_MAP.get(policy_major)

        if is_empty_or_unlimited(allowed_value):
            return make_result(True, "전공계열 제한 없음")

        user_value = user.get("major_category")

        if user_value != allowed_value:
            return make_result(False, f"전공계열이 정책 조건({allowed_value})과 다름", user_value, allowed_value)

        return make_result(True, "전공계열 조건 충족", user_value, allowed_value)

    @staticmethod
    def _match_sbiz(user, policy):
        policy_sbiz = policy.get("sbizCd")

        if is_empty_or_unlimited(policy_sbiz):
            return make_result(True, "특수계층 제한 없음")

        policy_sbiz_codes = [c.strip() for c in str(policy_sbiz).split(",") if c.strip()]

        policy_values = []
        user_value = {
            "gender": user.get("gender"),
            "disability": user.get("disability"),
            "basic_livelihood": user.get("basic_livelihood"),
            "single_parent": user.get("single_parent"),
            "employment_status": user.get("employment_status"),
            "occupation": user.get("occupation"),
            "company_type": user.get("company_type"),
        }

        for code in policy_sbiz_codes:
            allowed_value = SBIZ_MAP.get(code)

            if is_empty_or_unlimited(allowed_value):
                return make_result(True, "특수계층 제한 없음", user_value, policy_values)

            policy_values.append({"code": code, "name": allowed_value})

            if allowed_value == "기타":
                return make_result(True, "기타 조건은 자동 판단 어려움으로 통과", user_value, policy_values)

            checker = SBIZ_USER_CHECK.get(allowed_value)

            if checker and checker(user):
                return make_result(True, f"{allowed_value} 조건 충족", user_value, policy_values)

        return make_result(False, "특수계층 조건 불충족", user_value, policy_values)

    @staticmethod
    def _match_job(user, policy):
        policy_job = policy.get("jobCd")

        if is_empty_or_unlimited(policy_job):
            return make_result(True, "취업 상태 제한 없음")

        policy_job_codes = [c.strip() for c in str(policy_job).split(",") if c.strip()]
        user_status = user.get("employment_status")
        # 군인은 별도 취업상태 코드가 없어 '기타' 코드로 취급합니다(군필/미필 여부는 보지 않음).
        job_check_status = "기타" if user_status == "군인" else user_status

        policy_values = []

        for code in policy_job_codes:
            allowed_value = JOB_MAP.get(code)

            if is_empty_or_unlimited(allowed_value):
                return make_result(True, "취업 상태 제한 없음", user_status, policy_job)

            policy_values.append({"code": code, "name": allowed_value})

            if code == "0013006":
                if user.get("startup_interest") is True or user.get("occupation") == "창업자":
                    return make_result(True, "창업 관련 조건 충족", user_status, policy_values)

            if job_check_status == allowed_value:
                return make_result(True, "취업 상태 조건 충족", user_status, policy_values)

        return make_result(False, "취업 상태 조건 불충족", user_status, policy_values)
