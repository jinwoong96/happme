// className들을 조건부로 합친다(falsy 값은 제외).
export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

// 숫자를 "1,234,567원" 형식으로 표시한다.
export function formatCurrency(amount) {
  return new Intl.NumberFormat('ko-KR').format(amount) + '원';
}

// "2026-07-15" 같은 날짜 문자열을 "2026.07.15" 형식으로 바꾼다.
export function formatDate(dateStr) {
  if (!dateStr) return '';
  return dateStr.replace(/-/g, '.');
}
