import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const SPECIAL_CHAR_RULE = /[!@#$%^&*(),.?":{}|<>]/;
const MIN_LENGTH = 8;
const EMAIL_RULE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// 회원가입 폼 상태, 이메일 인증코드 발송/확인, 비밀번호 규칙 검증 및 제출을 관리한다.
export default function useSignup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    emailCode: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 이메일 인증 관련 상태
  const [emailSending, setEmailSending] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [emailVerifying, setEmailVerifying] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [emailMessage, setEmailMessage] = useState('');

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError('');
    // 이메일을 다시 수정하면 인증 상태 초기화
    if (name === 'email') {
      setEmailSent(false);
      setEmailVerified(false);
      setEmailMessage('');
    }
  };

  const handleSendCode = async () => {
    setEmailMessage('');
    if (!EMAIL_RULE.test(form.email)) {
      setEmailMessage('올바른 이메일 형식을 입력해주세요.');
      return;
    }
    setEmailSending(true);
    try {
      await api.post('/email/send-code', { email: form.email });
      setEmailSent(true);
      setEmailVerified(false);
      setEmailMessage('인증번호가 이메일로 전송되었습니다.');
    } catch (err) {
      setEmailMessage(err.message || '인증번호 전송에 실패했습니다.');
    } finally {
      setEmailSending(false);
    }
  };

  const handleVerifyCode = async () => {
    setEmailMessage('');
    if (!form.emailCode) {
      setEmailMessage('인증번호를 입력해주세요.');
      return;
    }
    setEmailVerifying(true);
    try {
      await api.post('/email/verify-code', { email: form.email, code: form.emailCode });
      setEmailVerified(true);
      setEmailMessage('이메일 인증이 완료되었습니다.');
    } catch (err) {
      setEmailVerified(false);
      setEmailMessage(err.message || '인증번호가 일치하지 않습니다.');
    } finally {
      setEmailVerifying(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    if (!emailVerified) {
      setError('이메일 인증을 완료해주세요.');
      return;
    }
    if (form.password.length < MIN_LENGTH) {
      setError(`비밀번호는 ${MIN_LENGTH}자 이상이어야 해요.`);
      return;
    }
    if (!SPECIAL_CHAR_RULE.test(form.password)) {
      setError('비밀번호에 특수문자를 1개 이상 포함해주세요.');
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError('비밀번호가 일치하지 않아요.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/users/', {
        name: form.name || undefined,
        email: form.email,
        password: form.password,
      });
      navigate('/login');
    } catch (err) {
      setError(err.message || '회원가입에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return { 
    form, 
    loading, 
    error, 
    handleChange, 
    handleSignup,
    emailSending,
    emailSent,
    emailVerifying,
    emailVerified,
    emailMessage,
    handleSendCode,
    handleVerifyCode, 
  };
}