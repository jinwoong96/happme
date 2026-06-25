import { useNavigate } from 'react-router-dom';
import { ChevronLeft, FileText, Bot } from 'lucide-react';
import useSummary from '../../hooks/useSummary';

export default function SummaryPage() {
  const { files, loading, results, handleFileChange, handleSummarize } = useSummary();
  const navigate = useNavigate();
  const canAnalyze = !loading && files.length > 0;

  return (
    <div className="bg-[#f5f6fa] h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 pt-5 pb-4 bg-white">
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="m-0 text-[18px] font-bold text-[#111]">공고문 요약</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex gap-3 bg-blue-50 rounded-[16px] px-4 py-3.5 mb-5">
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="m-0 text-[13px] text-[#555] leading-relaxed">공고문 PDF를 올리면 AI가 핵심 내용을 요약하고 중요 정보를 정리해드려요.</p>
        </div>

        {/* 업로드 */}
        <label className="block cursor-pointer">
          <input type="file" accept=".pdf" multiple onChange={handleFileChange} className="hidden" />
          <div className="border-2 border-dashed border-gray-300 rounded-[24px] py-9 px-5 flex flex-col items-center gap-3 bg-white">
            <div className="w-[60px] h-[60px] rounded-[18px] bg-red-50 flex items-center justify-center">
              <FileText size={28} color="#f87171" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <>
                <p className="m-0 text-[14px] font-semibold text-[#555]">PDF 파일을 선택하세요</p>
                <p className="m-0 text-[12px] text-[#bbb]">공고문, 안내자료 등 PDF 형식 지원</p>
              </>
            ) : (
              <div className="text-center flex flex-col gap-1">
                {files.map((f) => (
                  <div key={f.name} className="flex items-center gap-1.5 justify-center">
                    <FileText size={14} color="#f87171" />
                    <p className="m-0 text-[13px] font-semibold text-[#333]">{f.name}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        <button
          onClick={handleSummarize}
          disabled={!canAnalyze}
          className={`mt-3.5 w-full py-4 rounded-[16px] text-[16px] font-bold border-none transition-all ${
            canAnalyze
              ? 'bg-gradient-to-br from-blue-400 to-blue-500 text-white cursor-pointer shadow-[0_6px_18px_rgba(59,130,246,0.35)]'
              : 'bg-gray-200 text-[#aaa] cursor-default'
          }`}
        >
          {loading ? '요약 중...' : '공고문 요약 시작'}
        </button>

        {results && (
          <div className="mt-6 flex flex-col gap-3">
            <div className="bg-white rounded-[18px] p-[18px] shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
              <p className="m-0 mb-1.5 text-[12px] text-blue-500 font-bold">📋 공고 제목</p>
              <p className="m-0 text-[15px] font-bold text-[#111]">{results.title}</p>
            </div>
            <div className="bg-white rounded-[18px] p-[18px] shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
              <p className="m-0 mb-2.5 text-[12px] text-blue-500 font-bold">✨ AI 요약</p>
              <p className="m-0 text-[13px] text-[#555] leading-loose">{results.summary}</p>
            </div>
            <div className="bg-white rounded-[18px] p-[18px] shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
              <p className="m-0 mb-3 text-[12px] text-blue-500 font-bold">🔑 핵심 정보</p>
              <div className="flex flex-col gap-2">
                {results.keyPoints.map((point, i) => (
                  <div key={i} className="flex gap-2.5 items-start">
                    <div className="w-5 h-5 rounded-full bg-blue-50 text-blue-500 text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {i + 1}
                    </div>
                    <p className="m-0 text-[13px] text-[#444] leading-relaxed">{point}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
