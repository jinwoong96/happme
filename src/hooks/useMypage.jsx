import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function useMypage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 임시: 백엔드 연결 전 mock
    setUser({
      name: localStorage.getItem('userName') || '홍길동',
      email: 'user@example.com',
      bookmarkCount: 3,
    });
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    navigate('/login');
  };

  return { user, handleLogout };
}
