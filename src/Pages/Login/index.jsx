import useLogin from '../../hooks/useLogin';
import { useNavigate } from 'react-router-dom';

function KakaoIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path
        d="M12 3.5C6.75 3.5 2.5 6.86 2.5 11c0 2.66 1.77 5 4.44 6.33-.2.71-.71 2.55-.82 2.95-.13.5.18.49.38.36.16-.1 2.53-1.72 3.56-2.42.63.09 1.28.14 1.94.14 5.25 0 9.5-3.36 9.5-7.5S17.25 3.5 12 3.5z"
        fill="#3C1E1E"
      />
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 48 48">
      <path
        fill="#FFC107"
        d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20 s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"
      />
      <path
        fill="#FF3D00"
        d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657 C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"
      />
      <path
        fill="#4CAF50"
        d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36 c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"
      />
      <path
        fill="#1976D2"
        d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002 l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"
      />
    </svg>
  );
}

export default function LoginPage() {
  const { form, loading, error, handleChange, handleLogin, handleGoogleLogin, handleKakaoLogin, handleNaverLogin } = useLogin();
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col items-center justify-center" style={{ backgroundColor: '#f5f6fa', padding: '0 32px' }}>
      {/* 로고 */}
      <div className="flex flex-col items-center mb-10">
        <div
          className="w-[72px] h-[72px] flex items-center justify-center mb-4"
          style={{
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
            borderRadius: 22,
            boxShadow: '0 8px 24px rgba(59,130,246,0.35)',
          }}
        >
          <span className="text-white text-[34px] font-extrabold">₩</span>
        </div>
        <h1 className="text-[24px] font-extrabold text-gray-900">청년혜택</h1>
        <p className="mt-1.5 text-[13px] text-gray-600">청년을 위한 모든 지원금을 한눈에</p>
      </div>

      {/* 폼 */}
      <form onSubmit={handleLogin} style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
        {[
          { name: 'email',    label: '이메일',  type: 'email',    ph: '이메일을 입력하세요' },
          { name: 'password', label: '비밀번호', type: 'password', ph: '비밀번호를 입력하세요' },
        ].map(({ name, label, type, ph }) => (
          <div key={name}>
            <p style={{ marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#374151' }}>{label}</p>
            <input
              name={name} type={type} value={form[name]}
              onChange={handleChange} placeholder={ph} required
              style={{
                width: '100%',
                padding: '14px 16px',
                borderRadius: 14,
                border: '1.5px solid #e5e7eb',
                fontSize: 14,
                backgroundColor: '#ffffff',
                outline: 'none',
                color: '#1f2937',
                appearance: 'none',
                WebkitAppearance: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>
        ))}

        {error && <p className="text-[13px] text-red-400 text-center">{error}</p>}

        <button
          type="submit" disabled={loading}
          style={{
            marginTop: 4,
            width: '100%',
            padding: '16px 0',
            borderRadius: 16,
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
            color: '#fff',
            fontSize: 16,
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 6px 18px rgba(59,130,246,0.38)',
          }}
        >
          {loading ? '로그인 중...' : '로그인'}
        </button>
      </form>

      <p className="mt-5 text-[13px] text-gray-400">
        계정이 없으신가요?{' '}
        <span onClick={() => navigate('/signup')} className="text-blue-500 font-bold cursor-pointer">회원가입</span>
      </p>

      <div className="flex items-center gap-2.5 w-full mt-10">
        <div className="flex-1 h-px bg-gray-100" />
        <span className="text-[12px] text-gray-400 whitespace-nowrap">SNS 계정으로 간편 로그인</span>
        <div className="flex-1 h-px bg-gray-100" />
      </div>

      <div className="flex gap-4 mt-6">
        {[
          { key: 'kakao',  icon: <KakaoIcon />,  bg: '#FEE500', onClick: handleKakaoLogin },
          { key: 'naver',  label: 'N', bg: '#03C75A', color: '#fff', onClick: handleNaverLogin },
          { key: 'google', icon: <GoogleIcon />, bg: '#fff', border: '1px solid #e5e7eb', onClick: handleGoogleLogin },
        ].map(({ key, icon, label, bg, color, border, onClick }) => (
          <button
            key={key}
            onClick={onClick}
            className="flex items-center justify-center"
            style={{
              width: 48, height: 48, borderRadius: '50%',
              backgroundColor: bg, color, border: border || 'none',
              fontSize: 16, fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
            }}
          >
            {icon || label}
          </button>
        ))}
      </div>
    </div>
  );
}