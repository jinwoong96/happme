import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ImageIcon, Bot } from 'lucide-react';
import useOCR from '../../hooks/useOCR';

export default function OCRPage() {
  const { files, loading, results, handleFileChange, handleAnalyze } = useOCR();
  const navigate = useNavigate();
  const canAnalyze = !loading && files.length > 0;

  return (
    <div style={{ background: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '20px 16px 16px', background: '#fff' }}>
        <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}>
          <ChevronLeft size={24} color="#333" />
        </button>
        <p style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#111' }}>공고문 이미지 분석</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        <div style={{ display: 'flex', gap: 12, background: '#eff6ff', borderRadius: 16, padding: '14px 16px', marginBottom: 20 }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Bot size={18} color="#fff" />
          </div>
          <p style={{ margin: 0, fontSize: 13, color: '#555', lineHeight: 1.6 }}>전단지·포스터 사진을 올리면 AI가 텍스트를 추출하고 정책을 비교해요.</p>
        </div>

        <label style={{ display: 'block', cursor: 'pointer' }}>
          <input type="file" accept="image/*" multiple onChange={handleFileChange} style={{ display: 'none' }} />
          <div style={{ border: '2px dashed #d1d5db', borderRadius: 24, padding: '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, background: '#fff' }}>
            <div style={{ width: 60, height: 60, borderRadius: 18, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ImageIcon size={28} color="#3b82f6" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <p style={{ margin: 0, fontSize: 13, color: '#aaa' }}>이미지를 선택하세요</p>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#333' }}>{files[0].name}</p>
                {files.length > 1 && <p style={{ margin: '4px 0 0', fontSize: 12, color: '#aaa' }}>{files.slice(1).map((f) => f.name).join(' · ')}</p>}
              </div>
            )}
          </div>
        </label>

        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze}
          style={{ marginTop: 14, width: '100%', padding: '16px', borderRadius: 16, background: canAnalyze ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb', color: canAnalyze ? '#fff' : '#aaa', fontSize: 16, fontWeight: 700, border: 'none', cursor: canAnalyze ? 'pointer' : 'default', boxShadow: canAnalyze ? '0 6px 18px rgba(59,130,246,0.35)' : 'none' }}
        >
          {loading ? '분석 중...' : '이미지 분석 시작'}
        </button>

        {results && (
          <div style={{ marginTop: 24, background: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
            <p style={{ margin: '0 0 8px', fontSize: 14, fontWeight: 700, color: '#111' }}>추출된 텍스트</p>
            <p style={{ margin: '0 0 16px', fontSize: 13, color: '#666', lineHeight: 1.6 }}>{results.extracted}</p>
            <p style={{ margin: '0 0 10px', fontSize: 14, fontWeight: 700, color: '#111' }}>매칭된 정책</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {results.matched.map((m) => (
                <div key={m} style={{ padding: '10px 14px', borderRadius: 12, background: '#eff6ff', color: '#3b82f6', fontSize: 13, fontWeight: 600 }}>{m}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
