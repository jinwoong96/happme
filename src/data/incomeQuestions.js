// bene_ai/app/services/recommendation/income_questions.py 와 키를 맞춰야 합니다.
// (질문 문구를 바꾸면 두 곳 다 같이 바꿔주세요.)
export const INCOME_QUESTIONS = {
  annual_income: { label: '현재 연소득은 얼마인가요?', type: 'number', unit: '원' },
  is_business_owner: { label: '사업자 등록이 되어 있나요?', type: 'boolean' },
  annual_sales: { label: '연매출은 얼마인가요?', type: 'number', unit: '원' },
  household_size: { label: '가구원 수는 몇 명인가요?', type: 'number', unit: '명' },
  household_income: { label: '가구 전체 월소득은 얼마인가요?', type: 'number', unit: '원', allowUnknown: true },
};

// household_income에서 "모르겠어요"를 누르면 이 값이 답변으로 들어간다.
// bene_ai/app/services/recommendation/income_questions.py의 UNKNOWN_ANSWER와 반드시 같은 문자열이어야 한다.
export const UNKNOWN_ANSWER = '모르겠어요';
