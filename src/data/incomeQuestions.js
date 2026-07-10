// bene_ai/app/services/recommendation/income_questions.py 와 키를 맞춰야 합니다.
// (질문 문구를 바꾸면 두 곳 다 같이 바꿔주세요.)
export const INCOME_QUESTIONS = {
  annual_income: { label: '현재 연소득은 얼마인가요?', type: 'number', unit: '원' },
  is_business_owner: { label: '사업자 등록이 되어 있나요?', type: 'boolean' },
  annual_sales: { label: '연매출은 얼마인가요?', type: 'number', unit: '원' },
  household_size: { label: '가구원 수는 몇 명인가요?', type: 'number', unit: '명' },
  household_income: { label: '가구 전체 월소득은 얼마인가요?', type: 'number', unit: '원' },
};
