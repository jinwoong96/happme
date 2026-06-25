import { useNavigate } from 'react-router-dom';
import { ChevronLeft, FileText, Bot } from 'lucide-react';
import useSummary from '../../hooks/useSummary';

export default function SummaryPage() {
  const { files, loading, results, handleFileChange, handleSummarize } = useSummary();
  const navigate = useNavigate();
  const can = !loading && files.length > 0;

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">공고문 요약</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">공고문 PDF를 올리면 AI가 핵심 내용을 요약하고 중요 정보를 정리해드려요.</p>
        </div>

        <label style={{ display: 'block', cursor: 'pointer' }}>
          <input type="file" accept=".pdf" multiple onChange={handleFileChange} className="hidden" />
          <div style={{ border: '2px dashed #d1d5db', borderRadius: 24, padding: '36px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, backgroundColor: '#fff' }}>
            <div className="w-[60px] h-[60px] rounded-[18px] bg-red-50 flex items-center justify-center">
              <FileText size={28} color="#f87171" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <>
                <p className="text-[14px] font-semibold text-gray-600">PDF 파일을 선택하세요</p>
                <p className="text-[12px] text-gray-300">공고문, 안내자료 등 PDF 형식 지원</p>
              </>
            ) : (
              <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {files.map(f => (
                  <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
                    <FileText size={14} color="#f87171" />
                    <p className="text-[13px] font-semibold text-gray-800">{f.name}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        <button onClick={handleSummarize} disabled={!can}
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
          {loading ? '요약 중...' : '공고문 요약 시작'}
        </button>

        {results && (
          <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { label: '📋 공고 제목', body: <p className="text-[15px] font-bold text-gray-900">{results.title}</p> },
              { label: '✨ AI 요약',   body: <p className="text-[13px] text-gray-600 leading-loose">{results.summary}</p> },
              {
                label: '🔑 핵심 정보',
                body: (
                  <div className="flex flex-col gap-2">
                    {results.keyPoints.map((pt, i) => (
                      <div key={i} className="flex gap-2.5 items-start">
                        <div className="w-5 h-5 rounded-full bg-blue-50 text-blue-500 text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5">{i + 1}</div>
                        <p className="text-[13px] text-gray-700 leading-relaxed">{pt}</p>
                      </div>
                    ))}
                  </div>
                ),
              },
            ].map(({ label, body }) => (
              <div key={label} style={{ backgroundColor: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                <p className="mb-2.5 text-[12px] text-blue-500 font-bold">{label}</p>
                {body}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
