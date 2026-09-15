import re

from app.services.recommendation.code_mapping import EARN_TYPE_MAP
from app.services.recommendation.income_questions import INCOME_QUESTIONS, UNKNOWN_ANSWER
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


def _manwon_to_won(value) -> float | None:
    """정책 데이터의 earnMinAmt/earnMaxAmt는 만원 단위로 내려온다(예: 5000 -> 5,000만원).
    실제 원 단위 비교/표시를 위해 10,000을 곱해서 변환한다."""
    if is_empty_or_unlimited(value):
        return None
    return float(value) * 10_000


def _fmt_amount(value) -> str:
    won = _manwon_to_won(value)
    if won is None:
        return "제한없음"
    return f"{int(won):,}원"


def _fmt_range(min_amt, max_amt) -> str:
    return f"{_fmt_amount(min_amt)} ~ {_fmt_amount(max_amt)}"


_INCOME_TEXT_KEYWORDS = ("소득",)


def _mentions_income_condition(policy: dict) -> bool:
    """earnCndSeCd가 '무관'/비어있음으로 등록돼 있어도, 실제 지원내용 원문(plcySprtCn/earnEtcCn)에
    소득 관련 표현이 있으면 구조화 필드가 잘못 등록됐을 가능성이 있다고 보고 True를 반환한다.
    (예: 한국고용정보원 전세보증금반환보증 정책이 earnCndSeCd=무관인데 본문엔 "연소득 5천만원 이하"가 있는 실제 사례)
    """
    text = f"{policy.get('plcySprtCn') or ''} {policy.get('earnEtcCn') or ''}"
    return any(keyword in text for keyword in _INCOME_TEXT_KEYWORDS)


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

        # 규칙 엔진으로 판단이 안 됐고(= annual_income/annual_sales 등 다른 쓸만한 답변이 없고),
        # 가구 전체 월소득을 "모르겠어요"로 답한 경우에만 상한선 안내로 폴백한다.
        # (annual_income처럼 이미 답변된 값이 있으면 그걸로 먼저 판정하는 게 맞고, household_income의
        # "모르겠어요"가 그 답변을 가려버리면 안 되기 때문에 rule_result 판단 이후로 순서를 미뤘다.)
        if answers.get("household_income") == UNKNOWN_ANSWER:
            return self._household_income_unknown_result(policy)

        eligible, reason = self._llm_judge(policy, answers)
        return {"eligible": eligible, "method": "llm", "reason": reason}

    # ---------- 1) 규칙 엔진 ----------

    @staticmethod
    def _household_income_unknown_result(policy: dict) -> dict:
        """공고문(earnCndSeCd/earnMaxAmt/earnEtcCn) 기준으로 가구 월소득 상한선만 안내한다."""
        earn_cnd = policy.get("earnCndSeCd")
        earn_type = EARN_TYPE_MAP.get(earn_cnd)

        if earn_type == "무관" or is_empty_or_unlimited(earn_cnd):
            if _mentions_income_condition(policy):
                # 구조화 필드는 "무관"이지만 지원내용 원문에 소득 관련 표현이 있어 데이터 오류로 의심됨.
                # 섣불리 지원 가능 처리하지 않고 원문을 직접 확인하도록 안내한다.
                return {
                    "eligible": None,
                    "method": "unknown_income",
                    "reason": "이 정책은 소득 조건이 '무관'으로 등록돼 있지만, 지원내용에 소득 관련 표현이 있어 정확하지 않을 수 있어요. 공고문의 소득 조건을 직접 확인해주세요.",
                }
            return {"eligible": True, "method": "rule", "reason": "이 정책은 소득 조건과 무관하게 지원 가능합니다."}

        max_amt_won = _manwon_to_won(policy.get("earnMaxAmt"))
        if earn_type == "연소득" and max_amt_won is not None:
            monthly_cap = max_amt_won / 12
            return {
                "eligible": None,
                "method": "unknown_income",
                "reason": f"가구 월소득이 {int(monthly_cap):,}원 이상이면 이 정책을 지원받을 수 없어요.",
            }

        # 숫자 상한이 없는(자유텍스트/중위소득 비율 등) 경우 공고문 원문을 그대로 안내한다.
        etc = policy.get("earnEtcCn")
        reason = (
            f"이 정책의 소득 조건은 다음과 같아요: {etc}"
            if etc
            else "이 정책은 소득 상한이 명시되어 있지 않아 정확한 판정이 어려워요. 공고문의 소득 조건을 직접 확인해주세요."
        )
        return {"eligible": None, "method": "unknown_income", "reason": reason}

    @staticmethod
    def _rule_based_check(policy: dict, answers: dict) -> tuple[bool, str] | None:
        earn_cnd = policy.get("earnCndSeCd")
        earn_type = EARN_TYPE_MAP.get(earn_cnd)

        if earn_type == "무관" or is_empty_or_unlimited(earn_cnd):
            if _mentions_income_condition(policy):
                # 구조화 필드는 "무관"이지만 지원내용 원문에 소득 관련 표현이 있어 데이터 오류로 의심됨.
                # 규칙 엔진으로 단정 짓지 말고 LLM이 원문을 보고 판단하게 위임한다.
                return None
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

        min_amt_won = _manwon_to_won(min_amt)
        max_amt_won = _manwon_to_won(max_amt)
        min_ok = min_amt_won is None or income >= min_amt_won
        max_ok = max_amt_won is None or income <= max_amt_won
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
[소득 조건 유형(구조화 필드, 부정확할 수 있음)]: {earn_type}
[소득 조건 상세 설명(earnEtcCn)]: {policy.get("earnEtcCn") or "(별도 설명 없음)"}
[소득 하한(구조화 필드)]: {_fmt_amount(policy.get("earnMinAmt"))}
[소득 상한(구조화 필드)]: {_fmt_amount(policy.get("earnMaxAmt"))}
[지원내용 원문(plcySprtCn) - 구조화 필드와 다르면 이 원문을 우선하세요]:
{policy.get("plcySprtCn") or "(내용 없음)"}

[사용자 답변]
{answers_text}

규칙:
1. 구조화 필드(소득 조건 유형/하한/상한)와 지원내용 원문이 서로 다르면, 지원내용 원문에 적힌 실제 소득 조건을 기준으로 판단하세요.
2. 위 정보와 사용자 답변을 비교해서 이 사용자가 이 정책에 소득 기준상 지원 가능한지 판단하세요.
3. 조건을 판단하기에 정보가 부족하면 사용자에게 불리하지 않도록 '가능'으로 판단하세요.
4. 반드시 아래 형식으로만 답하세요. 다른 말은 하지 마세요.

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
