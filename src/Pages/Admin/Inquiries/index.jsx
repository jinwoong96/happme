import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useAdminInquiries from '../../../hooks/useAdminInquiries';

const STATUS_LABEL = {
  PENDING: { label: '답변 대기', bg: '#fef3c7', color: '#d97706' },
  ANSWERED: { label: '답변 완료', bg: '#dcfce7', color: '#16a34a' },
};

function InquiryCard({ inquiry, onAnswer }) {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState(inquiry.answer || '');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const status = STATUS_LABEL[inquiry.status] || STATUS_LABEL.PENDING;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answer.trim()) {
      setError('답변 내용을 입력해주세요.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await onAnswer(inquiry.inquiry_id, answer);
      setOpen(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
      <div className="flex items-start justify-between">
        <div style={{ flex: 1, minWidth: 0 }}>
          <p className="text-[11px] text-gray-400 font-medium">{inquiry.inquiry_type}</p>
          <p className="mt-0.5 text-[14px] font-bold text-gray-900">{inquiry.title}</p>
        </div>
        <span className="text-[11px] font-bold" style={{ padding: '3px 9px', borderRadius: 999, flexShrink: 0, backgroundColor: status.bg, color: status.color }}>
          {status.label}
        </span>
      </div>
      <p className="mt-2 text-[13px] text-gray-600">{inquiry.content}</p>

      {inquiry.answer && !open && (
        <div style={{ marginTop: 10, padding: '10px 12px', borderRadius: 12, backgroundColor: '#f8f9ff' }}>
          <p className="text-[11px] font-bold text-blue-500">답변</p>
          <p className="mt-1 text-[12px] text-gray-600">{inquiry.answer}</p>
        </div>
      )}

      {open ? (
        <form onSubmit={handleSubmit} style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <textarea
            value={answer} onChange={(e) => setAnswer(e.target.value)}
            placeholder="답변 내용을 입력하세요" rows={4}
            style={{ width: '100%', padding: '10px 12px', borderRadius: 12, border: '1.5px solid #e5e7eb', fontSize: 13, backgroundColor: '#fff', outline: 'none', color: '#1f2937', resize: 'vertical', boxSizing: 'border-box', fontFamily: 'inherit' }}
          />
          {error && <p className="text-[12px] text-red-400">{error}</p>}
          <div className="flex gap-8">
            <button type="button" onClick={() => setOpen(false)} style={{ flex: 1, padding: '10px 0', borderRadius: 12, border: '1.5px solid #e5e7eb', backgroundColor: '#fff', color: '#6b7280', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
              취소
            </button>
            <button type="submit" disabled={submitting} style={{ flex: 1, padding: '10px 0', borderRadius: 12, border: 'none', backgroundColor: '#3b82f6', color: '#fff', fontSize: 13, fontWeight: 700, cursor: submitting ? 'default' : 'pointer', opacity: submitting ? 0.7 : 1 }}>
              {submitting ? '등록 중...' : (inquiry.answer ? '답변 수정' : '답변 등록')}
            </button>
          </div>
        </form>
      ) : (
        <button
          onClick={() => setOpen(true)}
          style={{ marginTop: 10, padding: '9px 0', width: '100%', borderRadius: 12, border: '1.5px solid #e5e7eb', backgroundColor: '#fff', color: '#3b82f6', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}
        >
          {inquiry.answer ? '답변 수정하기' : '답변하기'}
        </button>
      )}
    </div>
  );
}

export default function AdminInquiriesPage() {
  const navigate = useNavigate();
  const { inquiries, loading, error, answerInquiry } = useAdminInquiries();

  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate('/admin')} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">문의 관리</p>
      </div>

      <div style={{ padding: '16px 20px 24px' }}>
        {loading ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>불러오는 중...</div>
        ) : error ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#ef4444' }}>{error}</div>
        ) : inquiries.length === 0 ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>접수된 문의가 없어요.</div>
        ) : (
          <div className="flex flex-col gap-2.5">
            {inquiries.map((inquiry) => (
              <InquiryCard key={inquiry.inquiry_id} inquiry={inquiry} onAnswer={answerInquiry} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
