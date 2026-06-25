import { Bookmark } from 'lucide-react';
import useCategory from '../../hooks/useCategory';

const TAG_COLOR = {
  인기: { bg: '#fff0f0', color: '#f87171' },
  마감임박: { bg: '#fff7ed', color: '#fb923c' },
  신규: { bg: '#f0fdf4', color: '#4ade80' },
  교육: { bg: '#eff6ff', color: '#60a5fa' },
  취업: { bg: '#faf5ff', color: '#c084fc' },
};

export default function CategoryPage() {
  const { categories, activeTab, setActiveTab, items, bookmarks, toggleBookmark } = useCategory();

  return (
    <div style={{ background: '#f5f6fa' }}>
      <div style={{ padding: '20px 20px 16px', background: '#fff' }}>
        <p style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#111' }}>카테고리</p>
      </div>

      <div style={{ display: 'flex', gap: 8, padding: '12px 16px', background: '#fff', borderBottom: '1px solid #f0f0f0', overflowX: 'auto' }}>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveTab(cat)}
            style={{ padding: '8px 18px', borderRadius: 20, fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', border: 'none', cursor: 'pointer', background: activeTab === cat ? '#3b82f6' : '#f3f4f6', color: activeTab === cat ? '#fff' : '#666' }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', fontSize: 13, color: '#aaa' }}>항목이 없습니다.</div>
        ) : (
          items.map((item) => {
            const tag = TAG_COLOR[item.tag] || { bg: '#f3f4f6', color: '#9ca3af' };
            return (
              <div key={item.id} style={{ background: '#fff', borderRadius: 18, padding: '16px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
                <div style={{ flex: 1 }}>
                  <span style={{ display: 'inline-block', padding: '3px 9px', borderRadius: 8, fontSize: 11, fontWeight: 700, background: tag.bg, color: tag.color }}>{item.tag}</span>
                  <p style={{ margin: '8px 0 2px', fontSize: 15, fontWeight: 700, color: '#111' }}>{item.title}</p>
                  <p style={{ margin: 0, fontSize: 12, color: '#aaa' }}>{item.org}</p>
                  <p style={{ margin: '6px 0 0', fontSize: 16, fontWeight: 800, color: '#3b82f6' }}>{item.amount}</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6, marginLeft: 10 }}>
                  <button onClick={() => toggleBookmark(item.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}>
                    <Bookmark size={18} color={bookmarks.has(item.id) ? '#3b82f6' : '#ccc'} fill={bookmarks.has(item.id) ? '#3b82f6' : 'none'} />
                  </button>
                  <span style={{ fontSize: 11, color: '#ccc' }}>~{item.deadline}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
