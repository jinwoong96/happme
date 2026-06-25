import useLogin from '../../hooks/useLogin';

export default function LoginPage() {
  const { form, loading, error, handleChange, handleLogin } = useLogin();

  return (
    <div style={{
      height: '100%',
      background: '#f5f6fa',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '0 28px',
    }}>
      {/* 로고 */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 40 }}>
        <div style={{
          width: 72, height: 72,
          background: 'linear-gradient(145deg, #60a5fa, #3b82f6)',
          borderRadius: 22,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 16,
          boxShadow: '0 8px 24px rgba(59,130,246,0.35)',
        }}>
          <span style={{ color: '#fff', fontSize: 34, fontWeight: 800 }}>₩</span>
        </div>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: '#111' }}>청년혜택</h1>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: '#aaa' }}>청년을 위한 모든 지원금을 한눈에</p>
      </div>

      {/* 입력 폼 */}
      <form onSubmit={handleLogin} style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <p style={{ margin: '0 0 7px', fontSize: 13, fontWeight: 600, color: '#444' }}>아이디</p>
          <input
            name="id"
            value={form.id}
            onChange={handleChange}
            placeholder="아이디를 입력하세요"
            required
            style={{
              width: '100%', boxSizing: 'border-box',
              padding: '14px 16px',
              borderRadius: 14, border: '1.5px solid #ebebeb',
              fontSize: 14, background: '#fff', outline: 'none',
              color: '#222',
            }}
          />
        </div>
        <div>
          <p style={{ margin: '0 0 7px', fontSize: 13, fontWeight: 600, color: '#444' }}>비밀번호</p>
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            placeholder="비밀번호를 입력하세요"
            required
            style={{
              width: '100%', boxSizing: 'border-box',
              padding: '14px 16px',
              borderRadius: 14, border: '1.5px solid #ebebeb',
              fontSize: 14, background: '#fff', outline: 'none',
              color: '#222',
            }}
          />
        </div>

        {error && <p style={{ margin: 0, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>}

        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: 4,
            padding: '16px',
            borderRadius: 16,
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
            color: '#fff', fontSize: 16, fontWeight: 700,
            border: 'none', cursor: 'pointer',
            boxShadow: '0 6px 18px rgba(59,130,246,0.4)',
          }}
        >
          {loading ? '로그인 중...' : '로그인'}
        </button>
      </form>

      {/* 회원가입 */}
      <p style={{ marginTop: 20, fontSize: 13, color: '#aaa' }}>
        계정이 없으신가요?{' '}
        <span style={{ color: '#3b82f6', fontWeight: 700, cursor: 'pointer' }}>회원가입</span>
      </p>

      {/* 구분선 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', marginTop: 24 }}>
        <div style={{ flex: 1, height: 1, background: '#eee' }} />
        <span style={{ fontSize: 12, color: '#bbb', whiteSpace: 'nowrap' }}>SNS 계정으로 간편 로그인</span>
        <div style={{ flex: 1, height: 1, background: '#eee' }} />
      </div>

      {/* SNS 버튼 */}
      <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
        {[
          { label: 'K', bg: '#FEE500', color: '#3C1E1E', border: 'none' },
          { label: 'N', bg: '#03C75A', color: '#fff', border: 'none' },
          { label: 'G', bg: '#fff', color: '#555', border: '1.5px solid #e0e0e0' },
        ].map(({ label, bg, color, border }) => (
          <button key={label} style={{
            width: 48, height: 48, borderRadius: '50%',
            background: bg, color, border,
            fontSize: 16, fontWeight: 700, cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
