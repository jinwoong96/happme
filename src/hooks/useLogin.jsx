import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function useLogin() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ id: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // 임시: 백엔드 연결 전 mock 로그인
      await new Promise((r) => setTimeout(r, 800));
      localStorage.setItem('token', 'mock-token');
      localStorage.setItem('userName', form.id);
      navigate('/');
    } catch {
      setError('아이디 또는 비밀번호가 올바르지 않습니다.');
    } finally {
      setLoading(false);
    }
  };

  return { form, loading, error, handleChange, handleLogin };
}
