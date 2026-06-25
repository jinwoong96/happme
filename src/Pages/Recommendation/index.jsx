import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Sparkles, Bot } from 'lucide-react';
import useRecommendation from '../../hooks/useRecommendation';

export default function RecommendationPage() {
  const { scenario, setScenario, results, loading, handleAnalyze } = useRecommendation();
  const navigate = useNavigate();
  const canAnalyze = !loading && scenario.trim();

  return (
    <div style={{ background: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '20px 16px 16px', background: '#fff' }}>
        <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}>
          <ChevronLeft size={24} color="#333" />
        </button>
        <p style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#111' }}>맞춤형 지원금 추천</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        <div style={{ display: 'flex', gap: 12, background: '#eff6ff', borderRadius: 16, padding: '14px 16px', marginBottom: 20 }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Bot size={18} color="#fff" />
          </div>
          <p style={{ margin: 0, fontSize: 13, color: '#555', lineHeight: 1.6 }}>현재 상황과 미래 계획을 입력하면 AI가 최적의 지원금을 추천해요.</p>
        </div>

        <p style={{ margin: '0 0 8px', fontSize: 14, fontWeight: 600, color: '#333' }}>시나리오 입력</p>
        <textarea
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          placeholder={'예: 내년에 IT 회사 입사를 준비 중이고, 현재 SW 교육을\n받고 있습니다. 부모님과 따로 거주 중이며…'}
          rows={5}
          style={{ width: '100%', boxSizing: 'border-box', padding: '14px 16px', borderRadius: 16, border: '1.5px solid #e8e8e8', fontSize: 14, background: '#fff', outline: 'none', resize: 'none', lineHeight: 1.6, color: '#333' }}
        />

        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze}
          style={{ marginTop: 14, width: '100%', padding: '16px', borderRadius: 16, background: canAnalyze ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb', color: canAnalyze ? '#fff' : '#aaa', fontSize: 16, fontWeight: 700, border: 'none', cursor: canAnalyze ? 'pointer' : 'default', boxShadow: canAnalyze ? '0 6px 18px rgba(59,130,246,0.35)' : 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
        >
          <Sparkles size={18} />
          {loading ? '분석 중...' : 'AI 분석 시작'}
        </button>

        {results && (
          <div style={{ marginTop: 24 }}>
            <p style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 700, color: '#111' }}>추천 결과</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {results.map((r) => (
                <div key={r.id} style={{ background: '#fff', borderRadius: 16, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
                  <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#111' }}>{r.title}</p>
                  <p style={{ margin: '6px 0 0', fontSize: 12, color: '#888', lineHeight: 1.5 }}>{r.reason}</p>
                  <p style={{ margin: '8px 0 0', fontSize: 16, fontWeight: 800, color: '#3b82f6' }}>{r.amount}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
