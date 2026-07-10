import { useNavigate } from 'react-router-dom';
import { ChevronLeft, FileText, Bot, Link2, MessageCircle, Home } from 'lucide-react';
import useSummary from '../../hooks/useSummary';

export default function SummaryPage() {
  const {
      files, text, url, loading, results, error,
      question, answer, asking,
      handleFileChange, handleTextChange, handleUrlChange,
      handleSummarize, canSummarize,
      setQuestion, handleAsk,
      handleReset, 
  } = useSummary();
  const navigate = useNavigate();

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center justify-between bg-white" style={{ padding: '20px 20px 16px' }}>
          <div className="flex items-center gap-2">
              <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
                  <ChevronLeft size={24} color="#333" />
              </button>
              <p className="text-[18px] font-bold text-gray-900">공고문 요약</p>
          </div>
          <button onClick={() => navigate('/')} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
              <Home size={22} color="#333" />
          </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">공고문 텍스트, PDF, URL을 입력하면 AI가 핵심 내용을 자동으로 요약해요.</p>
        </div>

        <p className="text-[13px] font-semibold text-gray-700 mb-2">공고문 텍스트</p>
        <textarea
          value={text}
          onChange={handleTextChange}
          placeholder="공고문 내용을 여기에 붙여넣으세요..."
          style={{
            width: '100%', minHeight: 110, borderRadius: 16, border: '1px solid #e5e7eb',
            padding: '12px 14px', fontSize: 13, backgroundColor: '#fff', resize: 'vertical',
            marginBottom: 16,
          }}
        />

        <p className="text-[13px] font-semibold text-gray-700 mb-2">파일 업로드</p>
        <label style={{ display: 'block', cursor: 'pointer' }}>
          <input type="file" accept=".pdf" multiple onChange={handleFileChange} className="hidden" />
          <div style={{ border: '2px dashed #d1d5db', borderRadius: 24, padding: '28px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, backgroundColor: '#fff' }}>
            <div className="w-[52px] h-[52px] rounded-[16px] bg-red-50 flex items-center justify-center">
              <FileText size={24} color="#f87171" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <>
                <p className="text-[13px] font-semibold text-gray-600">PDF 파일을 선택하세요</p>
                <p className="text-[11px] text-gray-300">공고문, 안내자료 등 PDF 형식 지원</p>
              </>
            ) : (
              <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {files.map(f => (
                  <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
                    <FileText size={13} color="#f87171" />
                    <p className="text-[12px] font-semibold text-gray-800">{f.name}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </label>

        <p className="text-[13px] font-semibold text-gray-700 mt-4 mb-2">URL 입력</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, border: '1px solid #e5e7eb', borderRadius: 14, padding: '10px 14px', backgroundColor: '#fff' }}>
          <Link2 size={16} color="#9ca3af" />
          <input
            value={url}
            onChange={handleUrlChange}
            placeholder="URL을 입력하세요"
            style={{ flex: 1, border: 'none', outline: 'none', fontSize: 13 }}
          />
        </div>

        <button onClick={handleSummarize} disabled={!canSummarize}
          style={{
            marginTop: 18,
            width: '100%',
            padding: '16px 0',
            borderRadius: 16,
            background: canSummarize ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb',
            color: canSummarize ? '#fff' : '#9ca3af',
            fontSize: 16,
            fontWeight: 700,
            border: 'none',
            cursor: canSummarize ? 'pointer' : 'default',
            boxShadow: canSummarize ? '0 6px 18px rgba(59,130,246,0.38)' : 'none',
          }}>
          {loading ? '요약 중...' : 'AI 요약 시작'}
        </button>

        {error && (
          <p style={{ marginTop: 12, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>
        )}

        {results && (
          <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { label: results.candidates ? '🔍 관련 정책' : '📋 공고 제목', body: (
                  <>
                      <p className="text-[15px] font-bold text-gray-900">{results.title}</p>
                      {results.subtitle && (
                          <p className="text-[13px] text-gray-500 mt-1">{results.subtitle}</p>
                      )}
                  </>
              )},
              {
                label: '✨ AI 요약',
                body: results.candidates ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {results.candidates.map((candidate, index) => (
                      <div
                        key={index}
                        style={{
                          border: '1px solid #e5e7eb',
                          borderRadius: 12,
                          padding: 14,
                          background: '#fafafa',
                        }}
                      >
                        <p
                          style={{
                            fontWeight: 700,
                            fontSize: 15,
                            marginBottom: 10,
                          }}
                        >
                          {index + 1}. {candidate.policy_name}
                        </p>

                        {Object.entries(candidate.fields || {}).map(([label, value]) => (
                          <p
                            key={label}
                            style={{
                              fontSize: 13,
                              color: '#4b5563',
                              marginBottom: 6,
                              lineHeight: 1.6,
                            }}
                          >
                            <strong>{label}</strong>: {value}
                          </p>
                        ))}

                        {candidate.apply_url && candidate.apply_url.trim() !== "" && (
                          <button
                            onClick={() => window.open(candidate.apply_url, "_blank")}
                            style={{
                              marginTop: 12,
                              width: '100%',
                              padding: '10px',
                              border: 'none',
                              borderRadius: 10,
                              background: '#3b82f6',
                              color: '#fff',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            정책 신청하기
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {results.summaryLines.map((line, i) => (
                      <p key={i} className="text-[13px] text-gray-600 leading-relaxed">
                        {line}
                      </p>
                    ))}

                    {results.applyUrl && (
                      <button
                        onClick={() => window.open(results.applyUrl, "_blank")}
                        style={{
                          marginTop: 16,
                          width: '100%',
                          padding: '12px',
                          border: 'none',
                          borderRadius: 12,
                          background: '#3b82f6',
                          color: '#fff',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        정책 신청하기
                      </button>
                    )}
                  </div>
                ),
              },
            ].map(({ label, body }) => (
              <div key={label} style={{ backgroundColor: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                <p className="mb-2.5 text-[12px] text-blue-500 font-bold">{label}</p>
                {body}
              </div>
            ))}
            <div style={{ backgroundColor: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
              <p className="mb-2.5 text-[12px] text-blue-500 font-bold flex items-center gap-1">
                <MessageCircle size={14} /> 질문 입력
              </p>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="궁금한 점을 입력하세요"
                style={{ width: '100%', minHeight: 70, borderRadius: 12, border: '1px solid #e5e7eb', padding: '10px 12px', fontSize: 13, resize: 'vertical' }}
              />
              <button onClick={handleAsk} disabled={asking || !question.trim()}
                style={{
                  marginTop: 10, padding: '10px 16px', borderRadius: 12, border: 'none',
                  background: question.trim() ? '#3b82f6' : '#e5e7eb',
                  color: question.trim() ? '#fff' : '#9ca3af',
                  fontSize: 13, fontWeight: 700, cursor: question.trim() ? 'pointer' : 'default',
                }}>
                {asking ? '답변 생성 중...' : '질문하기'}
              </button>
              {answer && <p className="mt-3 text-[13px] text-gray-700 leading-relaxed">{answer}</p>}
            </div>
            {/* 질문 섹션 닫는 div 바로 아래 */}
            <button
                onClick={handleReset}
                style={{
                    width: '100%',
                    padding: '14px 0',
                    borderRadius: 16,
                    border: '2px solid #3b82f6',
                    background: '#fff',
                    color: '#3b82f6',
                    fontSize: 15,
                    fontWeight: 700,
                    cursor: 'pointer',
                }}
            >
                🔄 요약 다시하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}