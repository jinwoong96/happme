import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ImageIcon, Bot } from 'lucide-react';
import useOCR from '../../hooks/useOCR';

export default function OCRPage() {
  const { files, loading, results, handleFileChange, handleAnalyze } = useOCR();
  const navigate = useNavigate();
  const canAnalyze = !loading && files.length > 0;

  return (
    <div className="bg-[#f5f6fa] h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 pt-5 pb-4 bg-white">
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="m-0 text-[18px] font-bold text-[#111]">공고문 이미지 분석</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex gap-3 bg-blue-50 rounded-[16px] px-4 py-3.5 mb-5">
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="m-0 text-[13px] text-[#555] leading-relaxed">전단지·포스터 사진을 올리면 AI가 텍스트를 추출하고 정책을 비교해요.</p>
        </div>

        {/* 업로드 */}
        <label className="block cursor-pointer">
          <input type="file" accept="image/*" multiple onChange={handleFileChange} className="hidden" />
          <div className="border-2 border-dashed border-gray-300 rounded-[24px] py-10 px-5 flex flex-col items-center gap-3 bg-white">
            <div className="w-[60px] h-[60px] rounded-[18px] bg-blue-50 flex items-center justify-center">
              <ImageIcon size={28} color="#3b82f6" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <p className="m-0 text-[13px] text-[#aaa]">이미지를 선택하세요</p>
            ) : (
              <div className="text-center">
                <p className="m-0 text-[14px] font-semibold text-[#333]">{files[0].name}</p>
                {files.length > 1 && <p className="m-0 mt-1 text-[12px] text-[#aaa]">{files.slice(1).map((f) => f.name).join(' · ')}</p>}
              </div>
            )}
          </div>
        </label>

        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze}
          className={`mt-3.5 w-full py-4 rounded-[16px] text-[16px] font-bold border-none transition-all ${
            canAnalyze
              ? 'bg-gradient-to-br from-blue-400 to-blue-500 text-white cursor-pointer shadow-[0_6px_18px_rgba(59,130,246,0.35)]'
              : 'bg-gray-200 text-[#aaa] cursor-default'
          }`}
        >
          {loading ? '분석 중...' : '이미지 분석 시작'}
        </button>

        {results && (
          <div className="mt-6 bg-white rounded-[18px] p-[18px] shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
            <p className="m-0 mb-2 text-[14px] font-bold text-[#111]">추출된 텍스트</p>
            <p className="m-0 mb-4 text-[13px] text-[#666] leading-relaxed">{results.extracted}</p>
            <p className="m-0 mb-2.5 text-[14px] font-bold text-[#111]">매칭된 정책</p>
            <div className="flex flex-col gap-2">
              {results.matched.map((m) => (
                <div key={m} className="px-3.5 py-2.5 rounded-[12px] bg-blue-50 text-blue-500 text-[13px] font-semibold">{m}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
