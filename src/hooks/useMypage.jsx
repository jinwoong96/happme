import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

export default function useMypage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get('/users/me')
      .then((data) => {
        setUser({
          name: data.name || '사용자',
          email: data.email || '',
          bookmarkCount: 3,
          // 소셜 로그인(구글/카카오/네이버) 유저는 비밀번호가 없어 false로 내려옴
          hasPassword: data.has_password ?? true,
        });
      })
      .catch(() => {
        setUser({
          name: localStorage.getItem('username') || '사용자',
          email: '',
          bookmarkCount: 3,
          hasPassword: true,
        });
      });
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    navigate('/login');
  };

  return { user, handleLogout };
}