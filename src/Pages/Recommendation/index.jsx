import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Sparkles, Bot, Bookmark, ExternalLink } from 'lucide-react';
import useRecommendation from '../../hooks/useRecommendation';
import useBookmarks from '../../hooks/useBookmarks';
import Modal from '../../Components/Modal';

const TABS = [
  { key: 'available', label: '조건 만족', empty: '조건에 맞는 정책을 찾지 못했어요.' },
  { key: 'closed', label: '신청 마감', empty: '신청이 마감된 정책이 없어요.' },
  { key: 'expired', label: '신청기간 종료', empty: '신청기간이 종료된 정책이 없어요.' },
  { key: 'unavailable', label: '조건 불만족', empty: '조건이 맞지 않는 정책이 없어요.' },
];

function PolicyCard({ policy, onOpen, isBookmarked, onToggleBookmark, bookmarkDisabled, children }) {
  return (
    <div
      onClick={() => onOpen(policy.policy_id, policy.policy_name, isBookmarked)}
      style={{ cursor: 'pointer', backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}
    >
      <div className="flex justify-between items-start gap-2">
        <p className="text-[15px] font-bold text-gray-900">{policy.policy_name}</p>
        <button
          onClick={(e) => { e.stopPropagation(); onToggleBookmark(policy.policy_id); }}
          disabled={bookmarkDisabled || policy.policy_id == null}
          className="bg-transparent border-none p-0.5 shrink-0"
          style={{ cursor: bookmarkDisabled || policy.policy_id == null ? 'default' : 'pointer' }}
        >
          <Bookmark size={18} color={isBookmarked ? '#3b82f6' : '#ccc'} fill={isBookmarked ? '#3b82f6' : 'none'} />
        </button>
      </div>
      <p className="mt-1.5 text-[12px] text-gray-500 leading-relaxed">{policy.policy_summary}</p>
      {children}
    </div>
  );
}

export default function RecommendationPage() {
  const {
    scenario, setScenario, results, loading, error, handleAnalyze,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  } = useRecommendation();
  const { isBookmarked, toggleBookmark, loading: bookmarksLoading } = useBookmarks();
  const navigate = useNavigate();
  const can = !loading && scenario.trim();
  const [activeTab, setActiveTab] = useState('available');

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">맞춤형 지원금 추천</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">현재 상황과 미래 계획을 입력하면 AI가 최적의 지원금을 추천해요.</p>
        </div>

        <p style={{ marginBottom: 8, fontSize: 14, fontWeight: 600, color: '#374151' }}>시나리오 입력</p>
        <textarea
          value={scenario} onChange={(e) => setScenario(e.target.value)}
          placeholder={'예: 내년에 IT 회사 입사를 준비 중이고, 현재 SW 교육을\n받고 있습니다. 부모님과 따로 거주 중이며…'}
          rows={5}
          style={{
            width: '100%',
            padding: '14px 16px',
            borderRadius: 16,
            border: '1.5px solid #e5e7eb',
            fontSize: 14,
            backgroundColor: '#fff',
            outline: 'none',
            resize: 'none',
            lineHeight: 1.6,
            color: '#1f2937',
            appearance: 'none',
            WebkitAppearance: 'none',
            boxSizing: 'border-box',
            fontFamily: 'inherit',
          }}
        />

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
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            boxShadow: can ? '0 6px 18px rgba(59,130,246,0.38)' : 'none',
          }}>
          <Sparkles size={18} />
          {loading ? '분석 중...' : 'AI 분석 시작'}
        </button>

        {error && <p style={{ marginTop: 12, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>}

        {results && (
          <div style={{ marginTop: 24 }}>
            <p className="mb-3 text-[16px] font-bold text-gray-900">추천 결과</p>

            <div className="flex gap-1.5 overflow-x-auto no-scrollbar mb-3.5">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  style={{
                    padding: '7px 14px',
                    borderRadius: 999,
                    fontSize: 12.5,
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: activeTab === tab.key ? '#3b82f6' : '#f3f4f6',
                    color: activeTab === tab.key ? '#fff' : '#4b5563',
                  }}
                >
                  {tab.label} ({results[tab.key].length})
                </button>
              ))}
            </div>

            {results[activeTab].length === 0 ? (
              <p className="text-[13px] text-gray-400">{TABS.find((t) => t.key === activeTab).empty}</p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {results[activeTab].map((r) => (
                  <PolicyCard
                    key={r.plcyNo}
                    policy={r}
                    onOpen={openPolicy}
                    isBookmarked={isBookmarked(r.policy_id, r.is_bookmarked)}
                    onToggleBookmark={toggleBookmark}
                    bookmarkDisabled={bookmarksLoading}
                  >
                    {r.fail_reasons?.length > 0 && (
                      <ul className="mt-2" style={{ paddingLeft: 16, margin: 0 }}>
                        {r.fail_reasons.map((fr, i) => (
                          <li key={i} className="text-[11px] text-red-400 list-disc">{fr.reason}</li>
                        ))}
                      </ul>
                    )}
                  </PolicyCard>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <Modal isOpen={!!selectedPolicy} onClose={closePolicy} title={selectedPolicy?.plcyNm}>
        {selectedPolicy && (
          <div className="flex flex-col gap-4">
            <button
              onClick={() => toggleBookmark(selectedPolicy.policy_id)}
              disabled={bookmarksLoading || selectedPolicy.policy_id == null}
              className="flex items-center gap-1.5 bg-transparent border-none p-0 self-start"
              style={{ cursor: bookmarksLoading || selectedPolicy.policy_id == null ? 'default' : 'pointer' }}
            >
              <Bookmark
                size={18}
                color={isBookmarked(selectedPolicy.policy_id, selectedPolicy.is_bookmarked) ? '#3b82f6' : '#9ca3af'}
                fill={isBookmarked(selectedPolicy.policy_id, selectedPolicy.is_bookmarked) ? '#3b82f6' : 'none'}
              />
              <span className="text-[13px] font-semibold" style={{ color: isBookmarked(selectedPolicy.policy_id, selectedPolicy.is_bookmarked) ? '#3b82f6' : '#6b7280' }}>
                {isBookmarked(selectedPolicy.policy_id, selectedPolicy.is_bookmarked) ? '즐겨찾기 됨' : '즐겨찾기 추가'}
              </span>
            </button>

            {policyLoading ? (
              <p className="text-[13px] text-gray-400">불러오는 중...</p>
            ) : selectedPolicy.error ? (
              <p className="text-[13px] text-red-400">{selectedPolicy.error}</p>
            ) : (
              <>
                {selectedPolicy.plcyExplnCn && (
                  <div>
                    <p className="text-[13px] font-bold text-gray-700 mb-1">정책 설명</p>
                    <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.plcyExplnCn}</p>
                  </div>
                )}
                {selectedPolicy.plcySprtCn && (
                  <div>
                    <p className="text-[13px] font-bold text-gray-700 mb-1">지원 내용</p>
                    <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.plcySprtCn}</p>
                  </div>
                )}
                {(selectedPolicy.sprtTrgtMinAge != null || selectedPolicy.sprtTrgtMaxAge != null) && (
                  <div>
                    <p className="text-[13px] font-bold text-gray-700 mb-1">지원 대상 연령</p>
                    <p className="text-[13px] text-gray-600">{selectedPolicy.sprtTrgtMinAge}세 ~ {selectedPolicy.sprtTrgtMaxAge}세</p>
                  </div>
                )}
                {selectedPolicy.aplyYmd && (
                  <div>
                    <p className="text-[13px] font-bold text-gray-700 mb-1">신청 기간</p>
                    <p className="text-[13px] text-gray-600">{selectedPolicy.aplyYmd}</p>
                  </div>
                )}
                {selectedPolicy.plcyAplyMthdCn && (
                  <div>
                    <p className="text-[13px] font-bold text-gray-700 mb-1">신청 방법</p>
                    <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.plcyAplyMthdCn}</p>
                  </div>
                )}
                {selectedPolicy.sbmsnDcmntCn && (
                  <div>
                    <p className="text-[13px] font-bold text-gray-700 mb-1">제출 서류</p>
                    <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.sbmsnDcmntCn}</p>
                  </div>
                )}
                {selectedPolicy.aplyUrlAddr && (
                  <a
                    href={selectedPolicy.aplyUrlAddr}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1.5"
                    style={{ color: '#3b82f6', fontSize: 13, fontWeight: 700, textDecoration: 'none' }}
                  >
                    신청 바로가기 <ExternalLink size={14} />
                  </a>
                )}
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
