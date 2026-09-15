const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082';

// 서버 에러 응답을 사용자에게 보여줄 한국어 문구로 바꾼다.
function toFriendlyMessage(status, err) {
  if (Array.isArray(err?.detail)) {
    const first = err.detail[0];
    const field = first?.loc?.[first.loc.length - 1];
    if (field === 'email') return '올바른 이메일 형식이 아니에요.';
    if (field === 'password') return '비밀번호 형식을 확인해주세요.';
    return '입력하신 정보를 다시 확인해주세요.';
  }

  if (typeof err?.detail === 'string' && err.detail) {
    return err.detail;
  }

  switch (status) {
    case 400:
      return '요청을 처리할 수 없어요. 입력값을 확인해주세요.';
    case 401:
      return '이메일 또는 비밀번호가 올바르지 않아요.';
    case 404:
      return '요청하신 정보를 찾을 수 없어요.';
    case 500:
      return '일시적인 서버 오류가 발생했어요. 잠시 후 다시 시도해주세요.';
    default:
      return '알 수 없는 오류가 발생했어요. 잠시 후 다시 시도해주세요.';
  }
}


// JSON body로 백엔드에 요청을 보낸다. 로그인 토큰은 헤더가 아니라 httpOnly 쿠키로
// 자동 전달되므로(credentials: 'include') Authorization 헤더는 쓰지 않는다.
async function request(method, endpoint, body) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    credentials: 'include', // httpOnly 쿠키를 주고받기 위해 필수
    headers: {
      'Content-Type': 'application/json',
    },
    ...(body && { body: JSON.stringify(body) }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(toFriendlyMessage(res.status, err));
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// 파일 업로드(FormData)로 백엔드에 요청을 보낸다.
async function requestForm(method, endpoint, formData) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    credentials: 'include',
    body: formData, // FormData는 Content-Type을 직접 지정하면 안 됨
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(toFriendlyMessage(res.status, err));
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// 백엔드 호출용 공용 클라이언트. 모든 요청은 이 객체를 통해 나간다.
export const api = {
  get: (endpoint) => request('GET', endpoint),
  post: (endpoint, body) => request('POST', endpoint, body),
  put: (endpoint, body) => request('PUT', endpoint, body),
  patch: (endpoint, body) => request('PATCH', endpoint, body),
  delete: (endpoint) => request('DELETE', endpoint),
  postForm: (endpoint, formData) => requestForm('POST', endpoint, formData),
};

