import { useNavigate } from 'react-router-dom';
import { ChevronLeft, FileText, Bot } from 'lucide-react';
import useSummary from '../../hooks/useSummary';

export default function SummaryPage() {
  const { files, loading, results, handleFileChange, handleSummarize } = useSummary();
  const navigate = useNavigate();
  const canAnalyze = !loading && files.length > 0;

  return (
    <div style={{ background: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '20px 16px 16px', background: '#fff' }}>
        <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}>
          <ChevronLeft size={24} color="#333" />
        </button>
        <p style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#111' }}>공고문 요약</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        <div style={{ display: 'flex', gap: 12, background: '#eff6ff', borderRadius: 16, padding: '14px 16px', marginBottom: 20 }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Bot size={18} color="#fff" />
          </div>
          <p style={{ margin: 0, fontSize: 13, color: '#555', lineHeight: 1.6 }}>공고문 PDF를 올리면 AI가 핵심 내용을 요약하고 중요 정보를 정리해드려요.</p>
        </div>

        <label style={{ display: 'block', cursor: 'pointer' }}>
          <input type="file" accept=".pdf" multiple onChange={handleFileChange} style={{ display: 'none' }} />
          <div style={{ border: '2px dashed #d1d5db', borderRadius: 24, padding: '36px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, background: '#fff' }}>
            <div style={{ width: 60, height: 60, borderRadius: 18, background: '#fff1f1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={28} color="#f87171" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#555' }}>PDF 파일을 선택하세요</p>
                <p style={{ margin: 0, fontSize: 12, color: '#bbb' }}>공고문, 안내자료 등 PDF 형식 지원</p>
              </>
            ) : (
              <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {files.map((f) => (
                  <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
                    <FileText size={14} color="#f87171" />
                    <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: '#333' }}>{f.name}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        <button
          onClick={handleSummarize}
          disabled={!canAnalyze}
          style={{ marginTop: 14, width: '100%', padding: '16px', borderRadius: 16, background: canAnalyze ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb', color: canAnalyze ? '#fff' : '#aaa', fontSize: 16, fontWeight: 700, border: 'none', cursor: canAnalyze ? 'pointer' : 'default', boxShadow: canAnalyze ? '0 6px 18px rgba(59,130,246,0.35)' : 'none' }}
        >
          {loading ? '요약 중...' : '공고문 요약 시작'}
        </button>

        {results && (
          <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ background: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
              <p style={{ margin: '0 0 6px', fontSize: 12, color: '#3b82f6', fontWeight: 700 }}>📋 공고 제목</p>
              <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#111' }}>{results.title}</p>
            </div>
            <div style={{ background: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
              <p style={{ margin: '0 0 10px', fontSize: 12, color: '#3b82f6', fontWeight: 700 }}>✨ AI 요약</p>
              <p style={{ margin: 0, fontSize: 13, color: '#555', lineHeight: 1.7 }}>{results.summary}</p>
            </div>
            <div style={{ background: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
              <p style={{ margin: '0 0 12px', fontSize: 12, color: '#3b82f6', fontWeight: 700 }}>🔑 핵심 정보</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {results.keyPoints.map((point, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                    <div style={{ width: 20, height: 20, borderRadius: '50%', background: '#eff6ff', color: '#3b82f6', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 }}>
                      {i + 1}
                    </div>
                    <p style={{ margin: 0, fontSize: 13, color: '#444', lineHeight: 1.5 }}>{point}</p>
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
