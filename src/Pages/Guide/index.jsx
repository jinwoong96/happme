import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';

const STEPS = [
  {
    type: 'image',
    src: '/메인화면_맞춤추천.png',
    title: '1. 홈 화면에서 맞춤추천 선택',
    desc: '홈 화면에서 맞춤추천 메뉴를 눌러 시작해요.',
  },
  {
    type: 'video',
    src: '/이용가이드2.mp4',
    title: '2. 조건 입력하고 추천받기',
    desc: '간단한 정보를 입력하면 나에게 맞는 정책을 추천해줘요.',
  },
];

export default function GuidePage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const isLast = step === STEPS.length - 1;
  const current = STEPS[step];

  return (
    <div style={{ backgroundColor: '#fff', height: '100%', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '14px 20px', flexShrink: 0 }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={22} color="#333" />
        </button>
        <p className="flex-1 text-[16px] font-bold text-gray-900">이용 가이드</p>
      </div>

      <div style={{ flex: 1, minHeight: 0, padding: '12px 16px 14px', display: 'flex', flexDirection: 'column' }}>
        <div style={{
          flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column',
          backgroundColor: '#fff', borderRadius: 18, padding: 14, boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
        }}>
          <p className="text-[13px] font-bold text-gray-900" style={{ flexShrink: 0 }}>{current.title}</p>
          <p className="mt-0.5 text-[11px] text-gray-500" style={{ flexShrink: 0 }}>{current.desc}</p>

          <div style={{
            flex: 1, minHeight: 0, marginTop: 10, borderRadius: 12, overflow: 'hidden', backgroundColor: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {current.type === 'image' ? (
              <img src={current.src} alt={current.title} style={{ maxWidth: '100%', maxHeight: '100%', width: 'auto', height: 'auto', display: 'block' }} />
            ) : (
              <video key={current.src} src={current.src} controls autoPlay style={{ maxWidth: '100%', maxHeight: '100%', width: 'auto', height: 'auto', display: 'block' }} />
            )}
          </div>

          <div className="flex items-center justify-center gap-1.5" style={{ marginTop: 10, flexShrink: 0 }}>
            {STEPS.map((_, i) => (
              <span
                key={i}
                style={{
                  width: i === step ? 16 : 6, height: 6, borderRadius: 999,
                  backgroundColor: i === step ? '#3b82f6' : '#e5e7eb',
                  transition: 'all 0.2s',
                }}
              />
            ))}
          </div>

          <button
            onClick={() => (isLast ? navigate('/mypage') : setStep((s) => s + 1))}
            style={{
              width: '100%', marginTop: 10, padding: '11px 0', borderRadius: 12, flexShrink: 0,
              backgroundColor: '#3b82f6', color: '#fff', fontSize: 14, fontWeight: 700,
              border: 'none', cursor: 'pointer',
            }}
          >
            {isLast ? '확인' : '다음'}
          </button>
        </div>
      </div>
    </div>
  );
}
