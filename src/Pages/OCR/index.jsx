import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ImageIcon, Bot } from 'lucide-react';
import useOCR from '../../hooks/useOCR';

export default function OCRPage() {
  const { files, loading, results, handleFileChange, handleAnalyze } = useOCR();
  const navigate = useNavigate();
  const can = !loading && files.length > 0;

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">공고문 이미지 분석</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">전단지·포스터 사진을 올리면 AI가 텍스트를 추출하고 정책을 비교해요.</p>
        </div>

        <label style={{ display: 'block', cursor: 'pointer' }}>
          <input type="file" accept="image/*" multiple onChange={handleFileChange} className="hidden" />
          <div style={{ border: '2px dashed #d1d5db', borderRadius: 24, padding: '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, backgroundColor: '#fff' }}>
            <div className="w-[60px] h-[60px] rounded-[18px] bg-blue-50 flex items-center justify-center">
              <ImageIcon size={28} color="#3b82f6" strokeWidth={1.5} />
            </div>
            {files.length === 0
              ? <p className="text-[13px] text-gray-400">이미지를 선택하세요</p>
              : <div className="text-center">
                  <p className="text-[14px] font-semibold text-gray-800">{files[0].name}</p>
                  {files.length > 1 && <p className="mt-1 text-[12px] text-gray-400">{files.slice(1).map(f => f.name).join(' · ')}</p>}
                </div>
            }
          </div>
        </label>

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
            boxShadow: can ? '0 6px 18px rgba(59,130,246,0.38)' : 'none',
          }}>
          {loading ? '분석 중...' : '이미지 분석 시작'}
        </button>

        {results && (
          <div style={{ marginTop: 24, backgroundColor: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
            <p className="mb-2 text-[14px] font-bold text-gray-900">추출된 텍스트</p>
            <p className="mb-4 text-[13px] text-gray-600 leading-relaxed">{results.extracted}</p>
            <p className="mb-2.5 text-[14px] font-bold text-gray-900">매칭된 정책</p>
            <div className="flex flex-col gap-2">
              {results.matched.map(m => (
                <div key={m} style={{ padding: '10px 14px', borderRadius: 12, backgroundColor: '#eff6ff', color: '#3b82f6', fontSize: 13, fontWeight: 600 }}>{m}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
