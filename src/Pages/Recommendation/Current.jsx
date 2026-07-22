import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronDown, RefreshCw, Home, UserPen } from 'lucide-react';
import useCurrentRecommendation from '../../hooks/useCurrentRecommendation';
import useBookmarks from '../../hooks/useBookmarks';
import PolicyCard from '../../Components/PolicyCard';
import PolicyDetailModal from '../../Components/PolicyDetailModal';
import IncomeEligibilityModal from '../../Components/IncomeEligibilityModal';

// 범위가 좁은 것부터(시/군/구 -> 시/도 -> 광역) 기본으로 노출한다.
const TABS = [
  { key: 'local', label: '시/군/구' },
  { key: 'province', label: '시/도' },
  { key: 'wide', label: '광역' },
];

// policies는 이미 유사도 내림차순으로 정렬되어 들어온다. Map은 삽입 순서를 보존하므로
// 카테고리를 처음 등장한 순서 그대로 묶으면 자연스럽게 정렬된다.
function groupByCategory(policies) {
  const groups = new Map();
  for (const policy of policies) {
    const category = policy.category || '기타';
    if (!groups.has(category)) groups.set(category, []);
    groups.get(category).push(policy);
  }
  return Array.from(groups, ([category, policies]) => ({ category, policies }));
}

function getPeriodBadge(policy) {
  if (policy.apply_period_type === '상시') return { label: '상시', bg: '#dcfce7', color: '#16a34a' };
  return null;
}

export default function CurrentRecommendationPage() {
  const {
    results, loading, refreshing, error, refresh,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  } = useCurrentRecommendation();
  const { isBookmarked, toggleBookmark, loading: bookmarksLoading } = useBookmarks();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('local');
  const [collapsedCategories, setCollapsedCategories] = useState(new Set());
  const [incomeCheckPolicy, setIncomeCheckPolicy] = useState(null);

  const visibleTabs = results ? TABS.filter((tab) => (results[tab.key] || []).length > 0) : [];

  // 결과가 새로 나올 때마다 모든 카테고리를 기본 펼침 상태로 초기화하고, 활성 탭이 결과가
  // 없어 숨겨졌다면 보이는 탭 중 첫 번째로 옮겨준다.
  useEffect(() => {
    if (!results) return;
    setCollapsedCategories(new Set());

    if (visibleTabs.length > 0 && !visibleTabs.some((tab) => tab.key === activeTab)) {
      setActiveTab(visibleTabs[0].key);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [results]);

  const toggleCategory = (category) => {
    setCollapsedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="flex-1 text-[20px] font-bold text-gray-900">가능정책</p>
        <button
          onClick={refresh}
          disabled={loading || refreshing}
          className="bg-transparent border-none p-0 flex items-center"
          style={{ marginRight: 4, cursor: loading || refreshing ? 'default' : 'pointer' }}
        >
          <RefreshCw size={20} color="#333" style={{ opacity: loading || refreshing ? 0.4 : 1 }} />
        </button>
        <button onClick={() => navigate('/')} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <Home size={22} color="#333" />
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex items-center justify-between gap-2 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <p className="text-[13px] text-gray-600 leading-relaxed">내 프로필을 기준으로 지원 가능한 정책을 모아봤어요.</p>
          <button
            onClick={() => navigate('/recommendation/profile', { state: { from: 'current' } })}
            className="flex items-center gap-1 bg-transparent border-none cursor-pointer shrink-0"
            style={{ fontSize: 12.5, fontWeight: 700, color: '#3b82f6' }}
          >
            <UserPen size={14} /> 프로필 수정
          </button>
        </div>

        {loading ? (
          <p className="text-[13px] text-gray-400" style={{ textAlign: 'center', padding: '40px 0' }}>불러오는 중...</p>
        ) : error ? (
          <p style={{ fontSize: 13, color: '#ef4444', textAlign: 'center', padding: '40px 0' }}>{error}</p>
        ) : !results || visibleTabs.length === 0 ? (
          <p className="text-[13px] text-gray-400" style={{ textAlign: 'center', padding: '40px 0' }}>조건에 맞는 정책을 찾지 못했어요.</p>
        ) : (
          <>
            <div className="flex gap-1.5 overflow-x-auto no-scrollbar mb-3.5">
              {visibleTabs.map((tab) => (
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

            {(results[activeTab] || []).length > 0 && (
              <div className="flex flex-col gap-4">
                {groupByCategory(results[activeTab]).map(({ category, policies }) => {
                  const collapsed = collapsedCategories.has(category);
                  return (
                    <div key={category}>
                      <button
                        onClick={() => toggleCategory(category)}
                        className="flex items-center gap-1 bg-transparent border-none p-0 w-full"
                        style={{ cursor: 'pointer' }}
                      >
                        <p className="mb-2 text-[13px] font-bold text-gray-500">{category} ({policies.length})</p>
                        <ChevronDown
                          size={14}
                          color="#9ca3af"
                          style={{ marginBottom: 8, transform: collapsed ? 'rotate(-90deg)' : 'none', transition: 'transform 0.15s' }}
                        />
                      </button>
                      {!collapsed && (
                        <div className="flex flex-col gap-2.5">
                          {policies.map((r) => (
                            <PolicyCard
                              key={r.plcyNo}
                              policy={r}
                              badge={getPeriodBadge(r)}
                              onOpen={openPolicy}
                              isBookmarked={isBookmarked(r.policy_id, r.is_bookmarked)}
                              onToggleBookmark={toggleBookmark}
                              bookmarkDisabled={bookmarksLoading}
                              onCheckIncome={setIncomeCheckPolicy}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>

      <PolicyDetailModal
        selectedPolicy={selectedPolicy}
        policyLoading={policyLoading}
        isBookmarked={isBookmarked(selectedPolicy?.policy_id, selectedPolicy?.is_bookmarked)}
        onToggleBookmark={toggleBookmark}
        bookmarkDisabled={bookmarksLoading}
        onClose={closePolicy}
      />

      {incomeCheckPolicy && (
        <IncomeEligibilityModal
          plcyNo={incomeCheckPolicy.plcyNo}
          requiredFields={incomeCheckPolicy.required_fields}
          onClose={() => setIncomeCheckPolicy(null)}
        />
      )}
    </div>
  );
}