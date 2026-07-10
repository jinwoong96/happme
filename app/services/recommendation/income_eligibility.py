import re

from app.services.recommendation.code_mapping import EARN_TYPE_MAP
from app.services.recommendation.income_questions import INCOME_QUESTIONS
from app.services.recommendation.policy_loader import PolicyLoaderService
from app.services.recommendation.rule_helpers import is_empty_or_unlimited


def _to_number(value) -> float | None:
    """"3000만원", "30,000,000", 30000000 등을 숫자(원 단위)로 변환. 실패하면 None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace(",", "").replace("원", "")
    if not text:
        return None

    m = re.match(r"^(\d+(?:\.\d+)?)\s*(억|만)?$", text)
    if not m:
        try:
            return float(text)
        except ValueError:
            return None

    number, unit = m.groups()
    number = float(number)
    if unit == "억":
        number *= 100_000_000
    elif unit == "만":
        number *= 10_000
    return number


def _fmt_amount(value) -> str:
    if is_empty_or_unlimited(value):
        return "제한없음"
    return f"{int(value):,}원"


def _fmt_range(min_amt, max_amt) -> str:
    return f"{_fmt_amount(min_amt)} ~ {_fmt_amount(max_amt)}"


class IncomeEligibilityService:
    """
    정책별 소득 조건(earnCndSeCd/earnMinAmt/earnMaxAmt/earnEtcCn)과 사용자가 모달에서 입력한 답변을
    비교해 해당 정책에 지원 가능한지(YES/NO) 판정한다.

    1) 규칙 엔진으로 먼저 판단을 시도한다 (소득무관, 또는 숫자 상/하한이 명확한 연소득 기준).
    2) 규칙으로 판단이 안 되면(자유텍스트 기준, 가구소득 기반 중위소득 기준 등) watsonx LLM에
       정책의 소득 조건 원문(earnEtcCn)과 사용자 답변을 같이 주고 최종 판정을 맡긴다.

    watsonx 클라이언트는 별도로 만들지 않고 PdfSummaryService가 들고 있는 llm_model을 재사용한다
    (lifespan에서 한 번만 만든 연결을 여러 서비스가 공유하는 기존 패턴과 동일).
    """

    def __init__(self, policy_loader: PolicyLoaderService, llm_service):
        self.policy_loader = policy_loader
        self.llm_service = llm_service  # PdfSummaryService 인스턴스 (llm_model 재사용)

    def judge_svc(self, plcy_no: str, answers: dict) -> dict:
        policy = self.policy_loader.get_policy_by_plcyno(plcy_no)
        if policy is None:
            return {"eligible": None, "method": "not_found", "reason": "해당 정책을 찾을 수 없습니다."}

        rule_result = self._rule_based_check(policy, answers)
        if rule_result is not None:
            eligible, reason = rule_result
            return {"eligible": eligible, "method": "rule", "reason": reason}

        eligible, reason = self._llm_judge(policy, answers)
        return {"eligible": eligible, "method": "llm", "reason": reason}

    # ---------- 1) 규칙 엔진 ----------

    @staticmethod
    def _rule_based_check(policy: dict, answers: dict) -> tuple[bool, str] | None:
        earn_cnd = policy.get("earnCndSeCd")
        earn_type = EARN_TYPE_MAP.get(earn_cnd)

        if earn_type == "무관" or is_empty_or_unlimited(earn_cnd):
            return True, ""

        min_amt = policy.get("earnMinAmt")
        max_amt = policy.get("earnMaxAmt")
        has_numeric_bounds = not (is_empty_or_unlimited(min_amt) and is_empty_or_unlimited(max_amt))

        if earn_type != "연소득" or not has_numeric_bounds:
            # earnEtcCn 자유텍스트 기준이거나 숫자 상/하한이 없는 경우 -> LLM에 위임
            return None

        income, basis = IncomeEligibilityService._resolve_income_basis(answers)
        if income is None:
            # 판정에 필요한 숫자 답변이 없음 -> LLM에 위임 (질문 문구 재해석 등에 맡김)
            return None

        min_ok = is_empty_or_unlimited(min_amt) or income >= float(min_amt)
        max_ok = is_empty_or_unlimited(max_amt) or income <= float(max_amt)
        range_text = _fmt_range(min_amt, max_amt)

        if min_ok and max_ok:
            return True, f"{basis} {int(income):,}원으로 정책 기준({range_text})을 충족합니다."
        return False, f"{basis} {int(income):,}원이 정책 기준({range_text})을 벗어납니다."

    @staticmethod
    def _resolve_income_basis(answers: dict) -> tuple[float | None, str]:
        """사업자 여부에 따라 연매출/연소득 중 어떤 값을 기준으로 판단할지 정한다."""
        if answers.get("is_business_owner") is True and answers.get("annual_sales") is not None:
            sales = _to_number(answers.get("annual_sales"))
            if sales is not None:
                return sales, "연매출"

        if answers.get("annual_income") is not None:
            income = _to_number(answers.get("annual_income"))
            if income is not None:
                return income, "연소득"

        if answers.get("household_income") is not None:
            monthly = _to_number(answers.get("household_income"))
            if monthly is not None:
                return monthly * 12, "가구 연소득(월소득×12 환산)"

        return None, ""

    # ---------- 2) LLM 판정 ----------

    def _llm_judge(self, policy: dict, answers: dict) -> tuple[bool, str]:
        answers_text = "\n".join(
            f"- {INCOME_QUESTIONS.get(key, key)}: {value}"
            for key, value in answers.items()
            if value is not None and value != ""
        ) or "(입력된 답변 없음)"

        earn_type = EARN_TYPE_MAP.get(policy.get("earnCndSeCd"), "정보없음")

        prompt = f"""당신은 청년 정책의 소득 조건 충족 여부를 판정하는 전문가입니다.

[정책명]: {policy.get("plcyNm", "")}
[소득 조건 유형]: {earn_type}
[소득 조건 상세 설명]: {policy.get("earnEtcCn") or "(별도 설명 없음)"}
[소득 하한]: {_fmt_amount(policy.get("earnMinAmt"))}
[소득 상한]: {_fmt_amount(policy.get("earnMaxAmt"))}

[사용자 답변]
{answers_text}

규칙:
1. 위 소득 조건 설명과 사용자 답변을 비교해서 이 사용자가 이 정책에 소득 기준상 지원 가능한지 판단하세요.
2. 조건을 판단하기에 정보가 부족하면 사용자에게 불리하지 않도록 '가능'으로 판단하세요.
3. 반드시 아래 형식으로만 답하세요. 다른 말은 하지 마세요.

가능여부: 가능 또는 불가능
사유: (한 문장으로 간결하게)"""

        try:
            raw = self.llm_service.llm_model.generate_text(prompt=prompt)
        except Exception as e:
            print(f"[IncomeEligibilityService] watsonx 호출 오류: {e}")
            return True, "소득 조건을 자동으로 판단하지 못해 우선 지원 가능으로 안내합니다."

        verdict_match = re.search(r"가능여부\s*[:：]\s*(가능|불가능)", raw)
        reason_match = re.search(r"사유\s*[:：]\s*(.+)", raw)

        eligible = verdict_match.group(1) == "가능" if verdict_match else True
        reason = reason_match.group(1).strip() if reason_match else raw.strip()

        return eligible, reason
