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

export const EMPLOYMENT_OPTIONS = [
  { value: '재직', label: '재직' },
  { value: '자영업', label: '자영업' },
  { value: '미취업', label: '미취업' },
  { value: '취업준비생', label: '취업준비생' },
  { value: '프리랜서', label: '프리랜서' },
  { value: '일용근로자', label: '일용근로자' },
  { value: '예비창업', label: '예비창업' },
  { value: '창업자', label: '창업자' },
  { value: '단기근로자', label: '단기근로자' },
  { value: '영농종사자', label: '영농종사자' },
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

// code_mapping.py SBIZ_USER_CHECK("군인")과 맞춘 값(군필/현역만 매칭 대상)
export const MILITARY_OPTIONS = [
  { value: '미필', label: '미필' },
  { value: '현역', label: '현역' },
  { value: '군필', label: '군필' },
  { value: '면제', label: '면제' },
];

// rule engine에서 직접 참조하지 않는 필드 - code_master 라벨 그대로 사용
export const STUDENT_STATUS_OPTIONS = [
  { value: '재학', label: '재학' },
  { value: '휴학', label: '휴학' },
  { value: '졸업', label: '졸업' },
  { value: '졸업예정', label: '졸업예정' },
];

export const STARTUP_STATUS_OPTIONS = [
  { value: '관심있음', label: '관심있음' },
  { value: '준비중', label: '준비중' },
  { value: '운영중', label: '운영중' },
];

export const HOUSING_OPTIONS = [
  { value: '자가', label: '자가' },
  { value: '전세', label: '전세' },
  { value: '월세', label: '월세' },
  { value: '기숙사', label: '기숙사' },
  { value: '기타', label: '기타' },
];

export const YES_NO_OPTIONS = [
  { value: true, label: '예' },
  { value: false, label: '아니오' },
];
