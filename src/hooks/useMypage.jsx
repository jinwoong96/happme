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
        });
      })
      .catch(() => {
        setUser({
          name: localStorage.getItem('username') || '사용자',
          email: '',
          bookmarkCount: 3,
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