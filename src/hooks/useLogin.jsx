import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

export default function useLogin() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.email) {
      setError('이메일을 입력해주세요.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError('올바른 이메일 형식이 아니에요.');
      return;
    }
    if (!form.password) {
      setError('비밀번호를 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      const data = await api.post('/users/login', {
        email: form.email,
        password: form.password,
      });
      localStorage.setItem('isAuthed', 'true');
      if (data?.user?.name) {
        localStorage.setItem('userName', data.user.name);
      }
      navigate('/');
    } catch (err) {
      setError(err.message || '이메일 또는 비밀번호가 올바르지 않습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:8082/auth/google/login';
  };

  const handleKakaoLogin = () => {
    window.location.href = 'http://localhost:8082/auth/kakao/login';
  };

  const handleNaverLogin = () => {
    window.location.href = 'http://localhost:8082/auth/naver/login';
  };

  return { form, loading, error, handleChange, handleLogin, handleGoogleLogin, handleKakaoLogin, handleNaverLogin };
}