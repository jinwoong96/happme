import { useState, useEffect } from 'react';
import { api } from '../utils/api';

// 로그인 여부를 서버에 물어봐서(/users/me) status('loading'|'authed'|'unauthed')와
// role을 알려준다. 성공하면 localStorage에도 사용자 정보를 캐싱하고, 실패하면 지운다.
export default function useAuth() {
  const [status, setStatus] = useState('loading');
  const [role, setRole] = useState(() => localStorage.getItem('userRole') || null);

  useEffect(() => {
    api.get('/users/me')
      .then((data) => {
        localStorage.setItem('isAuthed', 'true');
        if (data?.name) localStorage.setItem('userName', data.name);
        if (data?.email) localStorage.setItem('userEmail', data.email);
        if (data?.role) localStorage.setItem('userRole', data.role);
        setRole(data?.role || null);
        setStatus('authed');
      })
      .catch(() => {
        localStorage.removeItem('isAuthed');
        localStorage.removeItem('userName');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userRole');
        setRole(null);
        setStatus('unauthed');
      });
  }, []);

  return { status, role };
}