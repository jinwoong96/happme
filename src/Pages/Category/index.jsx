import { Bookmark } from 'lucide-react';
import useCategory from '../../hooks/useCategory';

const TAG = {
  인기:   'bg-red-50 text-red-400',
  마감임박: 'bg-orange-50 text-orange-400',
  신규:   'bg-green-50 text-green-400',
  교육:   'bg-blue-50 text-blue-400',
  취업:   'bg-purple-50 text-purple-400',
};

export default function CategoryPage() {
  const { categories, activeTab, setActiveTab, items, bookmarks, toggleBookmark } = useCategory();

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      <div className="bg-white" style={{ padding: '20px 20px 16px' }}>
        <p className="text-[22px] font-extrabold text-gray-900">카테고리</p>
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

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '14px 20px 24px' }}>
        {items.length === 0 ? (
          <div className="text-center py-10 text-[13px] text-gray-400">항목이 없습니다.</div>
        ) : items.map((item) => (
          <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
            <div style={{ flex: 1 }}>
              <span className={`inline-block px-2.5 py-0.5 rounded-lg text-[11px] font-bold ${TAG[item.tag] || 'bg-gray-100 text-gray-400'}`}>
                {item.tag}
              </span>
              <p className="mt-2 mb-0.5 text-[15px] font-bold text-gray-900">{item.title}</p>
              <p className="text-[12px] text-gray-400">{item.org}</p>
              <p className="mt-1.5 text-[16px] font-extrabold text-blue-500">{item.amount}</p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6, marginLeft: 10 }}>
              <button onClick={() => toggleBookmark(item.id)} className="bg-transparent border-none cursor-pointer p-0.5">
                <Bookmark size={18} color={bookmarks.has(item.id) ? '#3b82f6' : '#ccc'} fill={bookmarks.has(item.id) ? '#3b82f6' : 'none'} />
              </button>
              <span className="text-[11px] text-gray-300">~{item.deadline}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
