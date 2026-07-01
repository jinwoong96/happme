import { useNavigate } from 'react-router-dom';
import useSignup from '../../hooks/useSignup';

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  padding: '14px 16px',
  borderRadius: 14, border: '1.5px solid #ebebeb',
  fontSize: 14, background: '#fff', outline: 'none',
  color: '#222',
};

const labelStyle = { margin: '0 0 7px', fontSize: 13, fontWeight: 600, color: '#444' };

export default function SignupPage() {
  const {
    form, loading, error, handleChange, handleSignup,
    emailSending, emailSent, emailVerifying, emailVerified, emailMessage,
    handleSendCode, handleVerifyCode,
  } = useSignup();
  const navigate = useNavigate();

  return (
    <div style={{
      height: '100%', background: '#f5f6fa',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '0 28px',
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
        <div style={{
          width: 72, height: 72,
          background: 'linear-gradient(145deg, #60a5fa, #3b82f6)',
          borderRadius: 22, display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 16, boxShadow: '0 8px 24px rgba(59,130,246,0.35)',
        }}>
          <span style={{ color: '#fff', fontSize: 34, fontWeight: 800 }}>₩</span>
        </div>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: '#111' }}>회원가입</h1>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: '#aaa' }}>청년혜택과 함께 시작해보세요</p>
      </div>

      <form onSubmit={handleSignup} style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <p style={labelStyle}>이름</p>
          <input name="name" value={form.name} onChange={handleChange}
            placeholder="이름을 입력하세요" style={inputStyle} />
        </div>
        <div>
          <p style={labelStyle}>이메일</p>
          <div style={{ display: 'flex', gap: 8 }}>
            <input name="email" type="email" value={form.email} onChange={handleChange}
              placeholder="이메일을 입력하세요" required disabled={emailVerified}
              style={{ ...inputStyle, flex: 1, opacity: emailVerified ? 0.6 : 1 }} />
            <button type="button" onClick={handleSendCode} disabled={emailSending || emailVerified || !form.email}
              style={{
                whiteSpace: 'nowrap', padding: '0 16px', borderRadius: 14, border: 'none',
                background: emailVerified ? '#cbd5e1' : '#3b82f6', color: '#fff',
                fontSize: 13, fontWeight: 700, cursor: emailVerified ? 'default' : 'pointer',
              }}>
              {emailVerified ? '인증완료' : emailSending ? '전송 중...' : emailSent ? '재전송' : '인증번호 받기'}
            </button>
          </div>

          {emailSent && !emailVerified && (
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <input name="emailCode" value={form.emailCode} onChange={handleChange}
                placeholder="인증번호 6자리" style={{ ...inputStyle, flex: 1 }} />
              <button type="button" onClick={handleVerifyCode} disabled={emailVerifying}
                style={{
                  whiteSpace: 'nowrap', padding: '0 16px', borderRadius: 14, border: '1.5px solid #3b82f6',
                  background: '#fff', color: '#3b82f6', fontSize: 13, fontWeight: 700, cursor: 'pointer',
                }}>
                {emailVerifying ? '확인 중...' : '인증 확인'}
              </button>
            </div>
          )}

          {emailMessage && (
            <p style={{ margin: '6px 0 0', fontSize: 12, color: emailVerified ? '#16a34a' : '#ef4444' }}>
              {emailMessage}
            </p>
          )}
        </div>
        <div>
          <p style={labelStyle}>비밀번호</p>
          <input name="password" type="password" value={form.password} onChange={handleChange}
            placeholder="특수문자 포함, 8자 이상 입력하세요" required style={inputStyle} />
        </div>
        <div>
          <p style={labelStyle}>비밀번호 확인</p>
          <input name="confirmPassword" type="password" value={form.confirmPassword} onChange={handleChange}
            placeholder="비밀번호를 다시 입력하세요" required style={inputStyle} />
        </div>

        {error && <p style={{ margin: 0, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>}

        <button type="submit" disabled={loading || !emailVerified} style={{
          marginTop: 4, padding: '16px', borderRadius: 16,
          background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
          color: '#fff', fontSize: 16, fontWeight: 700,
          border: 'none', cursor: 'pointer',
          boxShadow: '0 6px 18px rgba(59,130,246,0.4)',
        }}>
          {loading ? '가입 중...' : '회원가입'}
        </button>
      </form>

      <p style={{ marginTop: 20, fontSize: 13, color: '#aaa' }}>
        이미 계정이 있으신가요?{' '}
        <span onClick={() => navigate('/login')} style={{ color: '#3b82f6', fontWeight: 700, cursor: 'pointer' }}>
          로그인
        </span>
      </p>
    </div>
  );
}