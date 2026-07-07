import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Search } from 'lucide-react';
import useNotification from '../../hooks/useNotification';

export default function NotificationPage() {
  const { filtered, search, setSearch, toggle, loading, isEmpty } = useNotification();
  const navigate = useNavigate();

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">지원금 알림</p>
      </div>

      <div className="bg-white border-b border-gray-100" style={{ padding: '12px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, backgroundColor: '#f5f6fa', borderRadius: 14, padding: '11px 14px' }}>
          <Search size={16} color="#aaa" />
          <input
            value={search} onChange={(e) => setSearch(e.target.value)} placeholder="지원금 검색..."
            style={{
              flex: 1, border: 'none', backgroundColor: 'transparent',
              fontSize: 14, color: '#1f2937', outline: 'none',
              appearance: 'none', WebkitAppearance: 'none',
            }}
          />
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', backgroundColor: '#fff' }}>
        {loading
          ? <div className="text-center py-10 text-[13px] text-gray-400">불러오는 중...</div>
          : isEmpty
          ? <div className="text-center py-10 text-[13px] text-gray-400">즐겨찾기한 지원금이 없어요. 전체보기에서 관심있는 정책을 즐겨찾기 해보세요.</div>
          : filtered.length === 0
          ? <div className="text-center py-10 text-[13px] text-gray-400">검색 결과가 없습니다.</div>
          : filtered.map((item, i) => (
            <div key={item.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 20px',
              borderBottom: i < filtered.length - 1 ? '1px solid #f9fafb' : 'none',
            }}>
              <div style={{ flex: 1, marginRight: 12 }}>
                <p className="text-[14px] font-semibold text-gray-900">{item.title}</p>
                <p className="mt-0.5 text-[12px] text-gray-400">{item.org ? `${item.org} · ` : ''}마감 {item.deadline}</p>
              </div>
              <button onClick={() => toggle(item.id)}
                style={{
                  width: 46, height: 26, borderRadius: 999, border: 'none', cursor: 'pointer',
                  backgroundColor: item.on ? '#3b82f6' : '#e5e7eb',
                  position: 'relative', flexShrink: 0, transition: 'background-color 0.2s',
                }}>
                <div style={{
                  position: 'absolute', top: 3,
                  left: item.on ? 23 : 3,
                  width: 20, height: 20, borderRadius: '50%', backgroundColor: '#fff',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
                  transition: 'left 0.2s',
                }} />
              </button>
            </div>
          ))
        }
      </div>
    </div>
  );
}
