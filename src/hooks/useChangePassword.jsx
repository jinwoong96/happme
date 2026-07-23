import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const SPECIAL_CHAR_RULE = /[!@#$%^&*(),.?":{}|<>]/;
const MIN_LENGTH = 8;

// 비밀번호 변경 폼 상태와 제출 처리를 관리한다.
export default function useChangePassword() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [checking, setChecking] = useState(true);

  // 소셜 로그인(구글/카카오/네이버) 유저는 비밀번호가 없으므로
  // 메뉴 클릭이 아닌 URL 직접 접근으로 들어와도 마이페이지로 돌려보냄
  useEffect(() => {
    api.get('/users/me')
      .then((data) => {
        if (data.has_password === false) {
          navigate('/mypage', { replace: true });
          return;
        }
        setChecking(false);
      })
      .catch(() => {
        navigate('/mypage', { replace: true });
      });
  }, [navigate]);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.currentPassword) {
      setError('현재 비밀번호를 입력해주세요.');
      return;
    }
    if (form.newPassword.length < MIN_LENGTH) {
      setError(`새 비밀번호는 ${MIN_LENGTH}자 이상이어야 해요.`);
      return;
    }
    if (!SPECIAL_CHAR_RULE.test(form.newPassword)) {
      setError('새 비밀번호에 특수문자를 1개 이상 포함해주세요.');
      return;
    }
    if (form.newPassword !== form.confirmPassword) {
      setError('새 비밀번호가 일치하지 않아요.');
      return;
    }
    if (form.currentPassword === form.newPassword) {
      setError('기존 비밀번호와 동일한 비밀번호는 사용할 수 없어요.');
      return;
    }

    setLoading(true);
    try {
      await api.patch('/users/me/password', {
        current_password: form.currentPassword,
        new_password: form.newPassword,
        confirm_password: form.confirmPassword,
      });
      setSuccess(true);
      setTimeout(() => navigate('/mypage'), 1200);
    } catch (err) {
      setError(err.message || '비밀번호 변경에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return { form, loading, error, success, checking, handleChange, handleSubmit };
}