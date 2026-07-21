import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

export default function useMypage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    let ignore = false;

    Promise.all([
      api.get('/users/me').catch(() => null),
      api.get('/bookmarks/me').catch(() => []),
      api.get('/bookmarks/me/calendar').catch(() => []),
    ]).then(([data, bookmarks, calendar]) => {
      if (ignore) return;
      setUser({
        name: data?.name || localStorage.getItem('username') || '사용자',
        email: data?.email || '',
        bookmarkCount: (bookmarks || []).length,
        // 마감 알림을 켜둔 즐겨찾기 개수 (bookmarks/me/calendar의 alarm_yn 기준)
        alertCount: (calendar || []).filter((b) => b.alarm_yn).length,
        // 소셜 로그인(구글/카카오/네이버) 유저는 비밀번호가 없어 false로 내려옴
        hasPassword: data?.has_password ?? true,
      });
    });

    return () => { ignore = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    navigate('/login');
  };

  return { user, handleLogout };
}