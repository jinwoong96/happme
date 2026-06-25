import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Sparkles, Bot } from 'lucide-react';
import useRecommendation from '../../hooks/useRecommendation';

export default function RecommendationPage() {
  const { scenario, setScenario, results, loading, handleAnalyze } = useRecommendation();
  const navigate = useNavigate();
  const canAnalyze = !loading && scenario.trim();

  return (
    <div className="bg-[#f5f6fa] h-full flex flex-col">
      {/* 헤더 */}
      <div className="flex items-center gap-2 px-4 pt-5 pb-4 bg-white">
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="m-0 text-[18px] font-bold text-[#111]">맞춤형 지원금 추천</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {/* AI 안내 */}
        <div className="flex gap-3 bg-blue-50 rounded-[16px] px-4 py-3.5 mb-5">
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="m-0 text-[13px] text-[#555] leading-relaxed">현재 상황과 미래 계획을 입력하면 AI가 최적의 지원금을 추천해요.</p>
        </div>

        <p className="m-0 mb-2 text-[14px] font-semibold text-[#333]">시나리오 입력</p>
        <textarea
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          placeholder={'예: 내년에 IT 회사 입사를 준비 중이고, 현재 SW 교육을\n받고 있습니다. 부모님과 따로 거주 중이며…'}
          rows={5}
          className="w-full box-border px-4 py-3.5 rounded-[16px] border border-[#e8e8e8] text-[14px] bg-white outline-none resize-none leading-relaxed text-[#333]"
        />

        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze}
          className={`mt-3.5 w-full py-4 rounded-[16px] text-[16px] font-bold border-none flex items-center justify-center gap-2 transition-all ${
            canAnalyze
              ? 'bg-gradient-to-br from-blue-400 to-blue-500 text-white cursor-pointer shadow-[0_6px_18px_rgba(59,130,246,0.35)]'
              : 'bg-gray-200 text-[#aaa] cursor-default'
          }`}
        >
          <Sparkles size={18} />
          {loading ? '분석 중...' : 'AI 분석 시작'}
        </button>

        {/* 결과 */}
        {results && (
          <div className="mt-6">
            <p className="m-0 mb-3 text-[16px] font-bold text-[#111]">추천 결과</p>
            <div className="flex flex-col gap-2.5">
              {results.map((r) => (
                <div key={r.id} className="bg-white rounded-[16px] px-[18px] py-4 shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
                  <p className="m-0 text-[15px] font-bold text-[#111]">{r.title}</p>
                  <p className="m-0 mt-1.5 text-[12px] text-[#888] leading-relaxed">{r.reason}</p>
                  <p className="m-0 mt-2 text-[16px] font-extrabold text-blue-500">{r.amount}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
