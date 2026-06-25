import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Search } from 'lucide-react';
import useNotification from '../../hooks/useNotification';

export default function NotificationPage() {
  const { filtered, search, setSearch, toggle } = useNotification();
  const navigate = useNavigate();

  return (
    <div style={{ background: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '20px 16px 16px', background: '#fff' }}>
        <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}>
          <ChevronLeft size={24} color="#333" />
        </button>
        <p style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#111' }}>지원금 알림</p>
      </div>

      {/* 검색창 */}
      <div style={{ padding: '12px 16px', background: '#fff', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#f5f6fa', borderRadius: 14, padding: '11px 14px' }}>
          <Search size={16} color="#aaa" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="지원금 검색..."
            style={{ flex: 1, border: 'none', background: 'transparent', fontSize: 14, color: '#333', outline: 'none' }}
          />
        </div>
      </div>

      {/* 목록 */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', fontSize: 13, color: '#aaa' }}>검색 결과가 없습니다.</div>
        ) : (
          filtered.map((item, i) => (
            <div
              key={item.id}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '16px 20px',
                background: '#fff',
                borderBottom: i < filtered.length - 1 ? '1px solid #f5f5f5' : 'none',
              }}
            >
              <div style={{ flex: 1, marginRight: 12 }}>
                <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#111' }}>{item.title}</p>
                <p style={{ margin: '3px 0 0', fontSize: 12, color: '#aaa' }}>
                  {item.org} · 마감 {item.deadline}
                </p>
              </div>

              {/* 토글 스위치 */}
              <button
                onClick={() => toggle(item.id)}
                style={{
                  width: 46, height: 26, borderRadius: 13,
                  background: item.on ? '#3b82f6' : '#e5e7eb',
                  border: 'none', cursor: 'pointer',
                  position: 'relative', flexShrink: 0,
                  transition: 'background 0.2s',
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: 3, left: item.on ? 23 : 3,
                  width: 20, height: 20, borderRadius: '50%',
                  background: '#fff',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
                  transition: 'left 0.2s',
                }} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
