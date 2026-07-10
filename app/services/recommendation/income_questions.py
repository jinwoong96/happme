"""
소득 확인이 필요한 정책에서 사용자에게 물어볼 질문 문구.
policy_incomeRequired.required_fields에 들어가는 키와 1:1로 대응한다.
프론트 모달에서 보여줄 질문 문구도 이 키셋을 기준으로 맞춰야 한다.
"""

INCOME_QUESTIONS: dict[str, str] = {
    "annual_income": "현재 연소득은 얼마인가요?",
    "is_business_owner": "사업자 등록이 되어 있나요?",
    "annual_sales": "연매출은 얼마인가요?",
    "household_size": "가구원 수는 몇 명인가요?",
    "household_income": "가구 전체 월소득은 얼마인가요?",
}
