import useLogin from '../../hooks/useLogin';

export default function LoginPage() {
  const { form, loading, error, handleChange, handleLogin } = useLogin();

  return (
    <div className="h-full bg-[#f5f6fa] flex flex-col items-center justify-center px-7">
      {/* 로고 */}
      <div className="flex flex-col items-center mb-10">
        <div className="w-[72px] h-[72px] bg-gradient-to-br from-blue-400 to-blue-500 rounded-[22px] flex items-center justify-center mb-4 shadow-[0_8px_24px_rgba(59,130,246,0.35)]">
          <span className="text-white text-[34px] font-extrabold">₩</span>
        </div>
        <h1 className="m-0 text-[24px] font-extrabold text-[#111]">청년혜택</h1>
        <p className="mt-1.5 text-[13px] text-[#aaa]">청년을 위한 모든 지원금을 한눈에</p>
      </div>

      {/* 폼 */}
      <form onSubmit={handleLogin} className="w-full flex flex-col gap-3.5">
        <div>
          <p className="m-0 mb-1.5 text-[13px] font-semibold text-[#444]">아이디</p>
          <input
            name="id"
            value={form.id}
            onChange={handleChange}
            placeholder="아이디를 입력하세요"
            required
            className="w-full px-4 py-3.5 rounded-[14px] border border-[#ebebeb] text-[14px] bg-white outline-none text-[#222] box-border"
          />
        </div>
        <div>
          <p className="m-0 mb-1.5 text-[13px] font-semibold text-[#444]">비밀번호</p>
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            placeholder="비밀번호를 입력하세요"
            required
            className="w-full px-4 py-3.5 rounded-[14px] border border-[#ebebeb] text-[14px] bg-white outline-none text-[#222] box-border"
          />
        </div>

        {error && <p className="m-0 text-[13px] text-red-400 text-center">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="mt-1 w-full py-4 rounded-[16px] bg-gradient-to-br from-blue-400 to-blue-500 text-white text-[16px] font-bold border-none cursor-pointer shadow-[0_6px_18px_rgba(59,130,246,0.4)]"
        >
          {loading ? '로그인 중...' : '로그인'}
        </button>
      </form>

      {/* 회원가입 */}
      <p className="mt-5 text-[13px] text-[#aaa]">
        계정이 없으신가요?{' '}
        <span className="text-blue-500 font-bold cursor-pointer">회원가입</span>
      </p>

      {/* 구분선 */}
      <div className="flex items-center gap-2.5 w-full mt-6">
        <div className="flex-1 h-px bg-[#eee]" />
        <span className="text-[12px] text-[#bbb] whitespace-nowrap">SNS 계정으로 간편 로그인</span>
        <div className="flex-1 h-px bg-[#eee]" />
      </div>

      {/* SNS 버튼 */}
      <div className="flex gap-4 mt-4">
        {[
          { label: 'K', bg: 'bg-[#FEE500]', text: 'text-[#3C1E1E]', border: '' },
          { label: 'N', bg: 'bg-[#03C75A]', text: 'text-white', border: '' },
          { label: 'G', bg: 'bg-white', text: 'text-[#555]', border: 'border border-[#e0e0e0]' },
        ].map(({ label, bg, text, border }) => (
          <button key={label} className={`w-12 h-12 rounded-full ${bg} ${text} ${border} text-[16px] font-bold cursor-pointer shadow-[0_2px_8px_rgba(0,0,0,0.1)]`}>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
