import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronDown, Sparkles, Bot, Home } from 'lucide-react';
import useRecommendation from '../../hooks/useRecommendation';
import useBookmarks from '../../hooks/useBookmarks';
import PolicyCard from '../../Components/PolicyCard';
import PolicyDetailModal from '../../Components/PolicyDetailModal';
import IncomeEligibilityModal from '../../Components/IncomeEligibilityModal';
import { ChoiceButtonsWithInput } from '../../Components/ChoiceButtons';
import { REGION_CHOICE_OPTIONS, EMPLOYMENT_CHOICE_OPTIONS } from '../../data/codeOptions';

// 범위가 좁은 것부터(시/군/구 -> 시/도 -> 광역) 기본으로 노출한다.
const TABS = [
  { key: 'local', label: '시/군/구', empty: '조건에 맞는 시/군/구 단위 정책을 찾지 못했어요.' },
  { key: 'province', label: '시/도', empty: '조건에 맞는 시/도 단위 정책을 찾지 못했어요.' },
  { key: 'wide', label: '광역', empty: '조건에 맞는 광역(전국/여러 시·도) 단위 정책을 찾지 못했어요.' },
];

// policies는 이미 유사도 내림차순으로 정렬되어 들어온다. Map은 삽입 순서를 보존하므로
// 카테고리를 처음 등장한 순서 그대로 묶으면 "유사도 가장 높은 정책이 속한 카테고리부터"
// 자연스럽게 정렬되고, 각 카테고리 내부도 원래의 유사도 순서가 그대로 유지된다.
function groupByCategory(policies) {
  const groups = new Map();
  for (const policy of policies) {
    const category = policy.category || '기타';
    if (!groups.has(category)) groups.set(category, []);
    groups.get(category).push(policy);
  }
  return Array.from(groups, ([category, policies]) => ({ category, policies }));
}

// 상시는 카드 데이터의 apply_period_type을 봅니다.
// (특정기간이면서 아직 열려있는 경우엔 배지 없이 날짜만 보여줍니다.)
function getPeriodBadge(policy) {
  if (policy.apply_period_type === '상시') return { label: '상시', bg: '#dcfce7', color: '#16a34a' };
  return null;
}

export default function RecommendationPage() {
  const {
    regionChoice, setRegionChoice, regionText, setRegionText,
    employmentChoice, setEmploymentChoice, employmentOther, setEmploymentOther,
    situation, setSituation,
    canAnalyze, results, loading, error, handleAnalyze,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  } = useRecommendation();
  const { isBookmarked, toggleBookmark, loading: bookmarksLoading } = useBookmarks();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('local');
  const [collapsedCategories, setCollapsedCategories] = useState(new Set());
  const [incomeCheckPolicy, setIncomeCheckPolicy] = useState(null);

  // 결과가 없는 탭은 아예 숨긴다.
  const visibleTabs = results ? TABS.filter((tab) => (results[tab.key] || []).length > 0) : [];

  // 분석 결과가 새로 나올 때마다 모든 카테고리를 기본 접힘 상태로 초기화하고, 활성 탭이 결과가
  // 없어 숨겨졌다면(예: 이전엔 있던 탭이 이번엔 0건) 보이는 탭 중 첫 번째로 옮겨준다.
  useEffect(() => {
    if (!results) return;
    const allCategories = new Set();
    for (const tab of TABS) {
      for (const policy of results[tab.key] || []) {
        allCategories.add(policy.category || '기타');
      }
    }
    setCollapsedCategories(allCategories);

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
        <p className="flex-1 text-[20px] font-bold text-gray-900">맞춤형 정책 추천</p>
        <button onClick={() => navigate('/')} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <Home size={22} color="#333" />
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">현재 상황과 미래 계획을 입력하면 AI가 최적의 지원금을 추천해요.</p>
        </div>

        <p style={{ marginBottom: 8, fontSize: 14, fontWeight: 600, color: '#374151' }}>Q1. 지역이동을 하실 건가요?</p>
        <ChoiceButtonsWithInput
          options={REGION_CHOICE_OPTIONS}
          value={regionChoice}
          onChange={setRegionChoice}
          textValue={regionText}
          onTextChange={setRegionText}
          textPlaceholder="이동할 지역을 입력하세요 (예: 수원, 제주도)"
        />

        <p style={{ margin: '20px 0 8px', fontSize: 14, fontWeight: 600, color: '#374151' }}>Q2. 회사 관련 변화가 있나요?</p>
        <ChoiceButtonsWithInput
          options={EMPLOYMENT_CHOICE_OPTIONS}
          value={employmentChoice}
          onChange={setEmploymentChoice}
          textValue={employmentOther}
          onTextChange={setEmploymentOther}
          textPlaceholder="어떤 상황인지 입력하세요"
        />

        <p style={{ margin: '20px 0 8px', fontSize: 14, fontWeight: 600, color: '#374151' }}>Q3. 지금 상황을 자유롭게 설명해주세요</p>
        <textarea
          value={situation} onChange={(e) => setSituation(e.target.value)}
          placeholder={'예: 수원에 가서 살고 싶어. 무슨 혜택이 있을까?'}
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

        <button onClick={handleAnalyze} disabled={!canAnalyze}
          style={{
            marginTop: 14,
            width: '100%',
            padding: '16px 0',
            borderRadius: 16,
            background: canAnalyze ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb',
            color: canAnalyze ? '#fff' : '#9ca3af',
            fontSize: 16,
            fontWeight: 700,
            border: 'none',
            cursor: canAnalyze ? 'pointer' : 'default',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            boxShadow: canAnalyze ? '0 6px 18px rgba(59,130,246,0.38)' : 'none',
          }}>
          <Sparkles size={18} />
          {loading ? '분석 중...' : 'AI 분석 시작'}
        </button>

        {error && <p style={{ marginTop: 12, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>}

        {results && (
          <div style={{ marginTop: 24 }}>
            <p className="mb-3 text-[16px] font-bold text-gray-900">추천 결과</p>

            {visibleTabs.length === 0 ? (
              <p className="text-[13px] text-gray-400">조건에 맞는 정책을 찾지 못했어요.</p>
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
