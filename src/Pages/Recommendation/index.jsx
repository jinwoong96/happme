import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Sparkles, Bot } from 'lucide-react';
import useRecommendation from '../../hooks/useRecommendation';

export default function RecommendationPage() {
  const { scenario, setScenario, results, loading, handleAnalyze } = useRecommendation();
  const navigate = useNavigate();
  const can = !loading && scenario.trim();

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">맞춤형 지원금 추천</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">현재 상황과 미래 계획을 입력하면 AI가 최적의 지원금을 추천해요.</p>
        </div>

        <p style={{ marginBottom: 8, fontSize: 14, fontWeight: 600, color: '#374151' }}>시나리오 입력</p>
        <textarea
          value={scenario} onChange={(e) => setScenario(e.target.value)}
          placeholder={'예: 내년에 IT 회사 입사를 준비 중이고, 현재 SW 교육을\n받고 있습니다. 부모님과 따로 거주 중이며…'}
          rows={5}
          style={{
            width: '100%',
            padding: '14px 16px',
            borderRadius: 16,
            border: '1.5px solid #e5e7eb',
            fontSize: 14,
            backgroundColor: '#fff',
            outline: 'none',
            resize: 'none',
            lineHeight: 1.6,
            color: '#1f2937',
            appearance: 'none',
            WebkitAppearance: 'none',
            boxSizing: 'border-box',
            fontFamily: 'inherit',
          }}
        />

        <button onClick={handleAnalyze} disabled={!can}
          style={{
            marginTop: 14,
            width: '100%',
            padding: '16px 0',
            borderRadius: 16,
            background: can ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb',
            color: can ? '#fff' : '#9ca3af',
            fontSize: 16,
            fontWeight: 700,
            border: 'none',
            cursor: can ? 'pointer' : 'default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            boxShadow: can ? '0 6px 18px rgba(59,130,246,0.38)' : 'none',
          }}>
          <Sparkles size={18} />
          {loading ? '분석 중...' : 'AI 분석 시작'}
        </button>

        {results && (
          <div style={{ marginTop: 24 }}>
            <p className="mb-3 text-[16px] font-bold text-gray-900">추천 결과</p>
            <div className="flex flex-col gap-2.5">
              {results.map((r) => (
                <div key={r.id} style={{ backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                  <p className="text-[15px] font-bold text-gray-900">{r.title}</p>
                  <p className="mt-1.5 text-[12px] text-gray-500 leading-relaxed">{r.reason}</p>
                  <p className="mt-2 text-[16px] font-extrabold text-blue-500">{r.amount}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
