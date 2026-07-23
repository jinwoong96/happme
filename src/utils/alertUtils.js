// 성공 메시지를 보여준다. (추후 toast 라이브러리로 교체 예정, 지금은 alert)
export function showSuccess(message) {
  alert(message);
}

// 에러 메시지를 보여준다.
export function showError(message) {
  alert(message);
}

// 확인/취소를 묻는다. 확인이면 true.
export function showConfirm(message) {
  return window.confirm(message);
}
