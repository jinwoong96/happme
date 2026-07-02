import { Bookmark } from 'lucide-react';
import useCategory from '../../hooks/useCategory';
import { REGIONS } from '../../data/regions';

export default function CategoryPage() {
  const {
    categories,
    activeTab,
    setActiveTab,
    selectedRegion,
    setSelectedRegion,
    items,
    loading,
    bookmarks,
    toggleBookmark,
  } = useCategory();

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      <div className="bg-white" style={{ padding: '20px 20px 16px' }}>
        <p className="text-[22px] font-extrabold text-gray-900">전체보기</p>
      </div>

      <div className="bg-white border-b border-gray-100 overflow-x-auto" style={{ display: 'flex', gap: 8, padding: '12px 20px' }}>
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

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '14px 20px 24px' }}>
        {activeTab === '지역' && !selectedRegion ? (
          <div className="text-center py-10 text-[13px] text-gray-400">지역을 선택하면 해당 지역의 정책이 표시됩니다.</div>
        ) : loading ? (
          <div className="text-center py-10 text-[13px] text-gray-400">불러오는 중...</div>
        ) : items.length === 0 ? (
          <div className="text-center py-10 text-[13px] text-gray-400">항목이 없습니다.</div>
        ) : items.map((item) => (
          <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
            <div style={{ flex: 1 }}>
              <p className="text-[15px] font-bold text-gray-900">{item.plcyNm}</p>
              <p className="mt-1 text-[12px] text-gray-400">{item.aplyYmd}</p>
            </div>
            <button onClick={() => toggleBookmark(item.id)} className="bg-transparent border-none cursor-pointer p-0.5" style={{ marginLeft: 10 }}>
              <Bookmark size={18} color={bookmarks.has(item.id) ? '#3b82f6' : '#ccc'} fill={bookmarks.has(item.id) ? '#3b82f6' : 'none'} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
