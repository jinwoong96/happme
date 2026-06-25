export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

export function formatCurrency(amount) {
  return new Intl.NumberFormat('ko-KR').format(amount) + '원';
}

export function formatDate(dateStr) {
  if (!dateStr) return '';
  return dateStr.replace(/-/g, '.');
}
