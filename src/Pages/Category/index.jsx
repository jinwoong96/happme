import { Search, X } from 'lucide-react';
import useCategory from '../../hooks/useCategory';
import { REGIONS } from '../../data/regions';
import PolicyCard from '../../Components/PolicyCard';
import PolicyDetailModal from '../../Components/PolicyDetailModal';

// 전체보기는 신청 가능 여부를 판정하지 않고 정책을 그대로 나열하므로, 상시 여부만 배지로 보여준다.
function getBadge(policy) {
  return policy.apply_period_type === '상시' ? { label: '상시', bg: '#dcfce7', color: '#16a34a' } : null;
}

export default function CategoryPage() {
  const {
    categories,
    activeTab,
    setActiveTab,
    selectedRegion,
    setSelectedRegion,
    keyword,
    setKeyword,
    sortOptions,
    sortOption,
    setSortOption,
    includeClosed,
    setIncludeClosed,
    consonantGroups,
    consonant,
    setConsonant,
    items,
    loading,
    bookmarks,
    toggleBookmark,
    selectedPolicy,
    policyLoading,
    openPolicy,
    closePolicy,
  } = useCategory();

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      <div className="bg-white" style={{ padding: '20px 20px 16px' }}>
        <p className="text-[22px] font-extrabold text-gray-900">전체보기</p>
      </div>

      <div className="bg-white" style={{ padding: '0 20px 16px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={16} color="#9ca3af" style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="정책명 또는 키워드로 검색"
            style={{
              width: '100%',
              padding: '11px 36px',
              borderRadius: 999,
              border: '1px solid #e5e7eb',
              fontSize: 13,
              fontWeight: 500,
              color: '#374151',
              backgroundColor: '#f9fafb',
              boxSizing: 'border-box',
            }}
          />
          {keyword && (
            <button
              onClick={() => setKeyword('')}
              className="bg-transparent border-none cursor-pointer p-0"
              style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', display: 'flex' }}
            >
              <X size={16} color="#9ca3af" />
            </button>
          )}
        </div>
      </div>

      <div className="bg-white border-b border-gray-100 overflow-x-auto no-scrollbar" style={{ display: 'flex', gap: 8, padding: '12px 20px', WebkitOverflowScrolling: 'touch' }}>
        {categories.map((cat) => (
          <button key={cat} onClick={() => setActiveTab(cat)}
            style={{
              padding: '8px 18px',
              borderRadius: 999,
              fontSize: 13,
              fontWeight: 600,
              whiteSpace: 'nowrap',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: activeTab === cat ? '#3b82f6' : '#f3f4f6',
              color: activeTab === cat ? '#fff' : '#4b5563',
            }}>
            {cat}
          </button>
        ))}
      </div>

      {activeTab === '지역' && (
        <div className="bg-white" style={{ padding: '0 20px 14px' }}>
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: 12,
              border: '1px solid #e5e7eb',
              fontSize: 13,
              fontWeight: 600,
              color: '#374151',
              backgroundColor: '#f9fafb',
            }}
          >
            <option value="">지역을 선택해주세요</option>
            {REGIONS.map((r) => (
              <option key={r.code} value={r.code}>{r.name}</option>
            ))}
          </select>
        </div>
      )}

      <div className="flex justify-between items-center" style={{ padding: '14px 20px 0' }}>
        {sortOption === 'alpha' ? (
          <select
            value={consonant}
            onChange={(e) => setConsonant(e.target.value)}
            style={{
              padding: '7px 12px',
              borderRadius: 999,
              border: '1px solid #e5e7eb',
              fontSize: 12.5,
              fontWeight: 600,
              color: '#374151',
              backgroundColor: '#f9fafb',
            }}
          >
            {consonantGroups.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        ) : sortOption === 'deadline' ? <div /> : (
          <label className="flex items-center gap-1.5" style={{ fontSize: 12.5, fontWeight: 600, color: '#6b7280', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={includeClosed}
              onChange={(e) => setIncludeClosed(e.target.checked)}
            />
            마감된 정책 보기
          </label>
        )}
        <select
          value={sortOption}
          onChange={(e) => setSortOption(e.target.value)}
          style={{
            padding: '7px 12px',
            borderRadius: 999,
            border: '1px solid #e5e7eb',
            fontSize: 12.5,
            fontWeight: 600,
            color: '#374151',
            backgroundColor: '#f9fafb',
          }}
        >
          {sortOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '10px 20px 24px' }}>
        {activeTab === '지역' && !selectedRegion ? (
          <div className="text-center py-10 text-[13px] text-gray-400">지역을 선택하면 해당 지역의 정책이 표시됩니다.</div>
        ) : loading ? (
          <div className="text-center py-10 text-[13px] text-gray-400">불러오는 중...</div>
        ) : items.length === 0 ? (
          <div className="text-center py-10 text-[13px] text-gray-400">
            {keyword ? `'${keyword}'에 대한 검색 결과가 없습니다.` : '항목이 없습니다.'}
          </div>
        ) : items.map((item) => (
          <PolicyCard
            key={item.policy_id}
            policy={item}
            badge={getBadge(item)}
            onOpen={openPolicy}
            isBookmarked={bookmarks.has(item.policy_id)}
            onToggleBookmark={toggleBookmark}
          />
        ))}
      </div>

      <PolicyDetailModal
        selectedPolicy={selectedPolicy}
        policyLoading={policyLoading}
        isBookmarked={selectedPolicy ? bookmarks.has(selectedPolicy.policy_id) : false}
        onToggleBookmark={toggleBookmark}
        onClose={closePolicy}
      />
    </div>
  );
}