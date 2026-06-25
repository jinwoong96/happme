export function showSuccess(message) {
  // 추후 toast 라이브러리 연동
  alert(message);
}

export function showError(message) {
  alert(message);
}

export function showConfirm(message) {
  return window.confirm(message);
}
