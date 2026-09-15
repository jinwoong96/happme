// AI 서버 rule engine(code_mapping.py)이 기대하는 값과 맞춘 옵션 목록입니다.
// code_master의 코드값(M/F, MARRIED/SINGLE 등)이 아니라 한글 라벨을 그대로 저장합니다.

export const GENDER_OPTIONS = [
  { value: '남', label: '남' },
  { value: '여', label: '여' },
];

export const MARITAL_OPTIONS = [
  { value: '미혼', label: '미혼' },
  { value: '기혼', label: '기혼' },
];

// code_mapping.py JOB_MAP과 맞춘 취업상태 값
export const EMPLOYMENT_OPTIONS = [
  { value: '재직자', label: '재직자' },
  { value: '자영업자', label: '자영업자' },
  { value: '미취업자', label: '미취업자' },
  { value: '프리랜서', label: '프리랜서' },
  { value: '일용근로자', label: '일용근로자' },
  { value: '(예비)창업자', label: '(예비)창업자' },
  { value: '단기근로자', label: '단기근로자' },
  { value: '영농종사자', label: '영농종사자' },
  { value: '군인', label: '군인' },
  { value: '기타', label: '기타' },
];

// code_mapping.py SCHOOL_MAP과 맞춘 학력 값
export const EDUCATION_OPTIONS = [
  { value: '고졸 미만', label: '고졸 미만' },
  { value: '고교 재학', label: '고교 재학' },
  { value: '고졸 예정', label: '고졸 예정' },
  { value: '고교 졸업', label: '고교 졸업' },
  { value: '대학 재학', label: '대학 재학' },
  { value: '대졸 예정', label: '대졸 예정' },
  { value: '대학 졸업', label: '대학 졸업' },
  { value: '석·박사', label: '석·박사' },
  { value: '기타', label: '기타' },
];

// code_mapping.py MAJOR_MAP과 맞춘 전공계열 값
export const MAJOR_CATEGORY_OPTIONS = [
  { value: '인문계열', label: '인문계열' },
  { value: '사회계열', label: '사회계열' },
  { value: '상경계열', label: '상경계열' },
  { value: '이학계열', label: '이학계열' },
  { value: '공학계열', label: '공학계열' },
  { value: '예체능계열', label: '예체능계열' },
  { value: '농산업계열', label: '농산업계열' },
  { value: '기타', label: '기타' },
];

export const YES_NO_OPTIONS = [
  { value: true, label: '예' },
  { value: false, label: '아니오' },
];

// 시나리오 Q1: 지역이동 여부. bene_backend ScenarioRecommendationRequest.region_choice와 값이 일치해야 함.
export const REGION_CHOICE_OPTIONS = [
  { value: '지역 쓰기', label: '지역 쓰기', hasInput: true },
  { value: '지역 이동 안함', label: '지역 이동 안함' },
  { value: '미정', label: '미정' },
];

// 시나리오 Q2: 회사 관련 변화. bene_backend ScenarioRecommendationRequest.employment_choice와 값이 일치해야 함.
export const EMPLOYMENT_CHOICE_OPTIONS = [
  { value: '없음', label: '없음' },
  { value: '이직', label: '이직' },
  { value: '퇴사', label: '퇴사' },
  { value: '창업', label: '창업' },
  { value: '재직', label: '재직' },
  { value: '기타', label: '기타', hasInput: true },
];
