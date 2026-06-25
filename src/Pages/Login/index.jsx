import useLogin from '../../hooks/useLogin';

export default function LoginPage() {
  const { form, loading, error, handleChange, handleLogin } = useLogin();

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
        <p className="mt-1.5 text-[13px] text-gray-400">청년을 위한 모든 지원금을 한눈에</p>
      </div>

      {/* 폼 */}
      <form onSubmit={handleLogin} style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
        {[
          { name: 'id',       label: '아이디',  type: 'text',     ph: '아이디를 입력하세요' },
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
        <span className="text-blue-500 font-bold cursor-pointer">회원가입</span>
      </p>

      <div className="flex items-center gap-2.5 w-full mt-6">
        <div className="flex-1 h-px bg-gray-100" />
        <span className="text-[12px] text-gray-300 whitespace-nowrap">SNS 계정으로 간편 로그인</span>
        <div className="flex-1 h-px bg-gray-100" />
      </div>

      <div className="flex gap-4 mt-4">
        {[
          { label: 'K', bg: '#FEE500', color: '#3C1E1E' },
          { label: 'N', bg: '#03C75A', color: '#fff' },
          { label: 'G', bg: '#fff',    color: '#555', border: '1px solid #e5e7eb' },
        ].map(({ label, bg, color, border }) => (
          <button
            key={label}
            style={{
              width: 48, height: 48, borderRadius: '50%',
              backgroundColor: bg, color, border: border || 'none',
              fontSize: 16, fontWeight: 700, cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
            }}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
