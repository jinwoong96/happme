import { useNavigate } from 'react-router-dom';
import { ChevronLeft, CheckCircle2 } from 'lucide-react';
import useAdminNotify from '../../../hooks/useAdminNotify';

export default function AdminNotifyPage() {
  const navigate = useNavigate();
  const { form, loading, error, done, setDone, handleChange, handleSubmit } = useAdminNotify();

  if (done) {
    return (
      <div style={{ height: '100%', backgroundColor: '#f5f6fa', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 32px' }}>
        <CheckCircle2 size={56} color="#3b82f6" strokeWidth={1.6} />
        <p style={{ marginTop: 16, fontSize: 16, fontWeight: 700, color: '#111' }}>전체 회원에게 발송했어요</p>
        <p style={{ marginTop: 6, fontSize: 13, color: '#aaa', textAlign: 'center' }}>공지사항 게시판에도 등록되었어요.</p>
        <div className="flex gap-8" style={{ marginTop: 28 }}>
          <button onClick={() => setDone(false)} style={{ padding: '13px 22px', borderRadius: 14, border: '1.5px solid #e5e7eb', backgroundColor: '#fff', color: '#374151', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
            추가 발송
          </button>
          <button onClick={() => navigate('/admin')} style={{ padding: '13px 22px', borderRadius: 14, border: 'none', background: 'linear-gradient(135deg, #60a5fa, #3b82f6)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
            관리자 홈으로
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate('/admin')} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <div>
          <p className="text-[18px] font-bold text-gray-900">공지 · 알림 발송</p>
          <p className="mt-0.5 text-[12px] text-gray-400">전체 회원에게 공지사항 알림을 보냅니다</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ padding: '20px 20px 32px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <p style={{ marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#374151' }}>제목</p>
          <input
            name="title" type="text" value={form.title} onChange={handleChange}
            placeholder="공지 제목을 입력하세요" required
            style={{ width: '100%', padding: '14px 16px', borderRadius: 14, border: '1.5px solid #e5e7eb', fontSize: 14, backgroundColor: '#fff', outline: 'none', color: '#1f2937', boxSizing: 'border-box' }}
          />
        </div>
        <div>
          <p style={{ marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#374151' }}>내용</p>
          <textarea
            name="content" value={form.content} onChange={handleChange}
            placeholder="공지 내용을 입력하세요" required rows={8}
            style={{ width: '100%', padding: '14px 16px', borderRadius: 14, border: '1.5px solid #e5e7eb', fontSize: 14, backgroundColor: '#fff', outline: 'none', color: '#1f2937', resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit' }}
          />
        </div>

        <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
          <input type="checkbox" name="is_pinned" checked={form.is_pinned} onChange={handleChange} style={{ width: 16, height: 16 }} />
          <span className="text-[13px] text-gray-600 font-medium">공지사항 상단 고정</span>
        </label>

        {error && <p className="text-[13px] text-red-400 text-center">{error}</p>}

        <button
          type="submit" disabled={loading}
          style={{
            marginTop: 4, width: '100%', padding: '16px 0', borderRadius: 16,
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)', color: '#fff',
            fontSize: 16, fontWeight: 700, border: 'none', cursor: loading ? 'default' : 'pointer',
            opacity: loading ? 0.7 : 1,
            boxShadow: '0 6px 18px rgba(59,130,246,0.38)',
          }}
        >
          {loading ? '발송 중...' : '전체 회원에게 발송'}
        </button>
      </form>
    </div>
  );
}
