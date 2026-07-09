import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import useInquiryForm from '../../hooks/useInquiryForm';

export default function InquiryFormPage() {
  const { type } = useParams();
  const navigate = useNavigate();
  const { config, form, loading, error, submitted, handleChange, handleSubmit } = useInquiryForm(type);

  if (!config) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <p className="text-[14px] text-gray-400">존재하지 않는 문의 유형입니다.</p>
      </div>
    );
  }

  const { Icon } = config;

  if (submitted) {
    return (
      <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 32px' }}>
        <div style={{ width: 64, height: 64, borderRadius: '50%', backgroundColor: config.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
          <Icon size={28} color={config.color} strokeWidth={1.8} />
        </div>
        <p className="text-[17px] font-bold text-gray-900">문의가 접수되었습니다</p>
        <p className="mt-2 text-[13px] text-gray-400 text-center">빠른 시일 내에 답변드리겠습니다.</p>
        <button
          onClick={() => navigate('/support')}
          style={{
            marginTop: 28, padding: '14px 28px', borderRadius: 14,
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
            color: '#fff', fontSize: 14, fontWeight: 700, border: 'none', cursor: 'pointer',
          }}
        >
          고객센터로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%' }}>
      <div className="bg-white" style={{ padding: '20px 20px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <button onClick={() => navigate(-1)} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 4 }}>
          <ChevronLeft size={22} color="#374151" />
        </button>
        <div>
          <p className="text-[18px] font-extrabold text-gray-900">{config.title}</p>
          <p className="mt-0.5 text-[12px] text-gray-400">{config.desc}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ padding: '20px 20px 32px', display: 'flex', flexDirection: 'column', gap: 16 }}>
        {config.fields.map(({ name, label, type: inputType, placeholder }) => (
          <div key={name}>
            <p style={{ marginBottom: 6, fontSize: 13, fontWeight: 600, color: '#374151' }}>{label}</p>
            {inputType === 'textarea' ? (
              <textarea
                name={name} value={form[name]} onChange={handleChange}
                placeholder={placeholder} required rows={6}
                style={{
                  width: '100%', padding: '14px 16px', borderRadius: 14,
                  border: '1.5px solid #e5e7eb', fontSize: 14, backgroundColor: '#ffffff',
                  outline: 'none', color: '#1f2937', resize: 'vertical', boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
              />
            ) : (
              <input
                name={name} type="text" value={form[name]} onChange={handleChange}
                placeholder={placeholder} required
                style={{
                  width: '100%', padding: '14px 16px', borderRadius: 14,
                  border: '1.5px solid #e5e7eb', fontSize: 14, backgroundColor: '#ffffff',
                  outline: 'none', color: '#1f2937', boxSizing: 'border-box',
                }}
              />
            )}
          </div>
        ))}

        {error && <p className="text-[13px] text-red-400 text-center">{error}</p>}

        <button
          type="submit" disabled={loading}
          style={{
            marginTop: 4, width: '100%', padding: '16px 0', borderRadius: 16,
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)', color: '#fff',
            fontSize: 16, fontWeight: 700, border: 'none', cursor: 'pointer',
            boxShadow: '0 6px 18px rgba(59,130,246,0.38)',
          }}
        >
          {loading ? '제출 중...' : '문의 제출하기'}
        </button>
      </form>
    </div>
  );
}
