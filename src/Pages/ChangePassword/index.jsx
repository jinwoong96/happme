import { useNavigate } from 'react-router-dom';
import { ChevronLeft, CheckCircle2 } from 'lucide-react';
import useChangePassword from '../../hooks/useChangePassword';

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  padding: '14px 16px',
  borderRadius: 14, border: '1.5px solid #ebebeb',
  fontSize: 14, background: '#fff', outline: 'none',
  color: '#222',
};

const labelStyle = { margin: '0 0 7px', fontSize: 13, fontWeight: 600, color: '#444' };

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const { form, loading, error, success, checking, handleChange, handleSubmit } = useChangePassword();

  if (checking) return null;

  if (success) {
    return (
      <div style={{
        height: '100%', backgroundColor: '#f5f6fa',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        <CheckCircle2 size={56} color="#3b82f6" strokeWidth={1.6} />
        <p style={{ marginTop: 16, fontSize: 16, fontWeight: 700, color: '#111' }}>비밀번호가 변경되었어요</p>
        <p style={{ marginTop: 6, fontSize: 13, color: '#aaa' }}>마이페이지로 이동합니다...</p>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[20px] font-bold text-gray-900">비밀번호 변경</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 20px' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <p style={labelStyle}>현재 비밀번호</p>
            <input name="currentPassword" type="password" value={form.currentPassword} onChange={handleChange}
              placeholder="현재 비밀번호를 입력하세요" required style={inputStyle} />
          </div>
          <div>
            <p style={labelStyle}>새 비밀번호</p>
            <input name="newPassword" type="password" value={form.newPassword} onChange={handleChange}
              placeholder="특수문자 포함, 8자 이상 입력하세요" required style={inputStyle} />
          </div>
          <div>
            <p style={labelStyle}>새 비밀번호 확인</p>
            <input name="confirmPassword" type="password" value={form.confirmPassword} onChange={handleChange}
              placeholder="새 비밀번호를 다시 입력하세요" required style={inputStyle} />
          </div>

          {error && <p style={{ margin: 0, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>}

          <button type="submit" disabled={loading} style={{
            marginTop: 4, padding: '16px', borderRadius: 16,
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
            color: '#fff', fontSize: 16, fontWeight: 700,
            border: 'none', cursor: loading ? 'default' : 'pointer',
            opacity: loading ? 0.7 : 1,
            boxShadow: '0 6px 18px rgba(59,130,246,0.4)',
          }}>
            {loading ? '변경 중...' : '비밀번호 변경'}
          </button>
        </form>
      </div>
    </div>
  );
}
