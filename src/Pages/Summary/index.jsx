import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, FileText, Bot, Link2, MessageCircle, Bookmark, ChevronDown, ChevronUp, ExternalLink, CheckCircle2 } from 'lucide-react';
import useSummary from '../../hooks/useSummary';
import useBookmarks from '../../hooks/useBookmarks';


export default function SummaryPage() {
  const [expandedIndex, setExpandedIndex] = useState(null);
  const {
      files, text, url, loading, results, error,
      question, answer, asking,
      handleFileChange, handleRemoveFile, handleTextChange, handleUrlChange,
      handleSummarize, canSummarize,
      setQuestion, setAnswer, handleAsk,
      handleReset, policyId, setPolicyName, clearSummarySession,
  } = useSummary();
  const { isBookmarked, toggleBookmark } = useBookmarks();
  const navigate = useNavigate();
  const [activeCandidateIndex, setActiveCandidateIndex] = useState(null);

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
          <button onClick={() => { clearSummarySession(); navigate(-1); }} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
              <ChevronLeft size={24} color="#333" />
          </button>
          <p className="text-[20px] font-bold text-gray-900">공고문 요약</p>
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
          <input type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />
          <div style={{ position: 'relative', border: '2px dashed #d1d5db', borderRadius: 24, padding: '28px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, backgroundColor: '#fff' }}>
            {files.length > 0 && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                style={{
                  position: 'absolute', top: 10, right: 10, width: 26, height: 26,
                  borderRadius: '50%', border: 'none', backgroundColor: '#9ca3af', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0,
                }}
              >
                ✕
              </button>
            )}
            <div className="w-[52px] h-[52px] rounded-[16px] bg-blue-50 flex items-center justify-center">
                <FileText size={24} color="#3b82f6" strokeWidth={1.5} />
            </div>
            {files.length === 0 ? (
              <>
                <p className="text-[13px] font-semibold text-gray-600">PDF 파일을 선택하세요</p>
                <p className="text-[11px] text-gray-300">공고문, 안내자료 등 PDF 형식 지원</p>
              </>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
                <FileText size={13} color="#3b82f6" />
                <p className="text-[12px] font-semibold text-gray-800">{files[0].name}</p>
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

        {!results && !error && (
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
        )}

        {error && (
            <>
                <p style={{ marginTop: 12, fontSize: 13, color: '#ef4444', textAlign: 'center', whiteSpace: 'pre-line' }}>{error}</p>
                <button
                    onClick={handleReset}
                    style={{
                        marginTop: 12, width: '100%', padding: '14px 0', borderRadius: 16,
                        border: '2px solid #3b82f6', background: '#fff',
                        color: '#3b82f6', fontSize: 15, fontWeight: 700, cursor: 'pointer',
                    }}
                >
                    🔄 요약 다시하기
                </button>
            </>
        )}

        {results && (
          <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} color="#22c55e" />
                <p className="text-[14px] font-bold text-gray-900">
                  분석 완료 · 정책 {results.candidates ? results.candidates.length : 1}건 매칭
                </p>
              </div>
              <button
                onClick={() => navigate('/bookmark')}
                style={{
                  display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
                  padding: '6px 10px', borderRadius: 999, border: 'none',
                  backgroundColor: '#eff6ff', color: '#3b82f6', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                }}
              >
                <Bookmark size={13} />
                즐겨찾기 보기
              </button>
            </div>

            {[
              { label: results.candidates ? '관련 정책' : '공고 제목', body: (
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                      <div>
                          <p className="text-[15px] font-bold text-gray-900">{results.title}</p>
                          {results.subtitle && (
                              <p className="text-[13px] text-gray-500 mt-1">{results.subtitle}</p>
                          )}
                      </div>
                      {!results.candidates && policyId && (
                          <button
                              onClick={() => toggleBookmark(policyId)}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', flexShrink: 0 }}
                          >
                              <Bookmark
                                  size={20}
                                  color={isBookmarked(policyId) ? '#3b82f6' : '#9ca3af'}
                                  fill={isBookmarked(policyId) ? '#3b82f6' : 'none'}
                              />
                          </button>
                      )}
                  </div>
              )},
              {
                label: 'AI 요약',
                body: results.candidates ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {results.candidates.map((candidate, index) => {
                      const isOpen = expandedIndex === index;
                      return (
                        <div
                          key={index}
                          style={{ border: '1px solid #e5e7eb', borderRadius: 12, padding: 14, background: '#fafafa' }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                            <p
                              onClick={() => setExpandedIndex(isOpen ? null : index)}
                              style={{ fontWeight: 700, fontSize: 15, cursor: 'pointer', flex: 1, margin: 0 }}
                            >
                              {index + 1}. {candidate.policy_name}
                            </p>

                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              {candidate.policy_id && (
                                <button
                                  onClick={() => toggleBookmark(candidate.policy_id)}
                                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex' }}
                                >
                                  <Bookmark
                                    size={18}
                                    color={isBookmarked(candidate.policy_id) ? '#3b82f6' : '#9ca3af'}
                                    fill={isBookmarked(candidate.policy_id) ? '#3b82f6' : 'none'}
                                  />
                                </button>
                              )}

                              <button
                                onClick={() => setExpandedIndex(isOpen ? null : index)}
                                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex' }}
                              >
                                {isOpen ? <ChevronUp size={18} color="#9ca3af" /> : <ChevronDown size={18} color="#9ca3af" />}
                              </button>
                            </div>
                          </div>

                          {isOpen && (
                            <div style={{ marginTop: 10 }}>
                              {Object.entries(candidate.fields || {}).map(([label, value]) => (
                                <p
                                  key={label}
                                  style={{ fontSize: 13, color: '#4b5563', marginBottom: 6, lineHeight: 1.6 }}
                                >
                                  <strong>{label}</strong>: {value}
                                </p>
                              ))}

                              {candidate.apply_url && candidate.apply_url.trim() !== "" ? (
                                  <a
                                      href={candidate.apply_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      style={{
                                          marginTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                                          padding: '10px 0', borderRadius: 10, backgroundColor: '#eff6ff', color: '#3b82f6',
                                          fontSize: 13, fontWeight: 700, textDecoration: 'none',
                                      }}
                                  >
                                      공식 사이트
                                      <ExternalLink size={14} />
                                  </a>
                              ) : (
                                  <div style={{
                                      marginTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                      padding: '10px 0', borderRadius: 10, backgroundColor: '#f9fafb', color: '#c1c5cb',
                                      fontSize: 13, fontWeight: 700,
                                  }}>
                                      공식 사이트 정보 없음
                                  </div>
                              )}

                              {/* ✅ 이 정책에 질문하기 버튼 */}
                              <button
                                  onClick={() => {
                                      setPolicyName(candidate.policy_name);
                                      setQuestion('');
                                      setAnswer(null);
                                      setActiveCandidateIndex(index);
                                  }}
                                  style={{
                                      marginTop: 12, width: '100%', padding: '10px', border: '1px solid #3b82f6',
                                      borderRadius: 10, background: '#fff', color: '#3b82f6',
                                      fontWeight: 700, cursor: 'pointer',
                                  }}
                              >
                                  💬 이 정책에 질문하기
                              </button>

                              {/* ✅ 선택된 후보 카드에만 질문창 표시 */}
                              {activeCandidateIndex === index && (
                                  <div style={{ marginTop: 12 }}>
                                      <textarea
                                          value={question}
                                          onChange={(e) => setQuestion(e.target.value)}
                                          placeholder="궁금한 점을 입력하세요"
                                          style={{ width: '100%', minHeight: 70, borderRadius: 12, border: '1px solid #e5e7eb', padding: '10px 12px', fontSize: 13, resize: 'vertical' }}
                                      />
                                      <button onClick={handleAsk} disabled={asking || !question.trim()}
                                          style={{
                                              marginTop: 8, padding: '10px 16px', borderRadius: 12, border: 'none',
                                              background: question.trim() ? '#3b82f6' : '#e5e7eb',
                                              color: question.trim() ? '#fff' : '#9ca3af',
                                              fontSize: 13, fontWeight: 700, cursor: question.trim() ? 'pointer' : 'default',
                                          }}
                                      >
                                          {asking ? '답변 생성 중...' : '질문하기'}
                                      </button>
                                      {answer && <p style={{ marginTop: 10, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>{answer}</p>}
                                  </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {results.summaryLines.map((item, i) => (
                      <p key={i} className="text-[13px] text-gray-600 leading-relaxed">
                        {item.label ? (
                          <>
                            <strong>{i + 1}. {item.label}</strong>: {item.value}
                          </>
                        ) : (
                          item.value
                        )}
                      </p>
                    ))}

                    {results.applyUrl ? (
                        <a
                            href={results.applyUrl}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                                marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                                padding: '12px 0', borderRadius: 12, backgroundColor: '#eff6ff', color: '#3b82f6',
                                fontSize: 13, fontWeight: 700, textDecoration: 'none',
                            }}
                        >
                            공식 사이트
                            <ExternalLink size={14} />
                        </a>
                    ) : (
                        <div style={{
                            marginTop: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            padding: '12px 0', borderRadius: 12, backgroundColor: '#f9fafb', color: '#c1c5cb',
                            fontSize: 13, fontWeight: 700,
                        }}>
                            공식 사이트 정보 없음
                        </div>
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
            {!results.candidates && (
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
            )}
            {/* 질문 섹션 닫는 div 바로 아래 */}
            <button
                onClick={() => {
                    handleReset();
                    setActiveCandidateIndex(null);  // ← 추가
                }}
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
                요약 다시하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}