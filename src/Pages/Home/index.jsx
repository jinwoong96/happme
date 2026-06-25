import { useNavigate } from 'react-router-dom';
import useHome from '../../hooks/useHome';
import { Bell, RefreshCw, List, Sparkles, FileText, ScanSearch, BellRing, Bookmark, ChevronRight } from 'lucide-react';

const MENU = [
  { label: '카테고리', path: '/category', Icon: List },
  { label: '맞춤추천', path: '/recommendation', Icon: Sparkles },
  { label: '공고요약', path: '/summary', Icon: FileText },
  { label: 'OCR분석', path: '/ocr', Icon: ScanSearch },
  { label: '지원금알림', path: '/notification', Icon: BellRing },
  { label: '즐겨찾기', path: '/bookmark', Icon: Bookmark },
];

const TAG_COLOR = {
  인기: { bg: '#fff0f0', color: '#f87171' },
  마감임박: { bg: '#fff7ed', color: '#fb923c' },
  신규: { bg: '#f0fdf4', color: '#4ade80' },
  교육: { bg: '#eff6ff', color: '#60a5fa' },
  취업: { bg: '#faf5ff', color: '#c084fc' },
};

export default function HomePage() {
  const { benefits, featured, loading, userName } = useHome();
  const navigate = useNavigate();

  return (
    <div style={{ background: '#f5f6fa' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '20px 20px 16px', background: '#fff' }}>
        <div>
          <p style={{ margin: 0, fontSize: 13, color: '#aaa', fontWeight: 400 }}>안녕하세요</p>
          <p style={{ margin: '2px 0 0', fontSize: 22, fontWeight: 800, color: '#111' }}>{userName}님 👋</p>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <button style={{ width: 38, height: 38, borderRadius: '50%', border: '1.5px solid #eee', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <Bell size={18} color="#555" />
          </button>
          <button style={{ width: 38, height: 38, borderRadius: '50%', border: '1.5px solid #eee', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
            <RefreshCw size={16} color="#555" />
          </button>
        </div>
      </div>

      <div style={{ padding: '16px 16px 0' }}>
        {/* 추천 배너 */}
        {featured && (
          <div style={{ background: 'linear-gradient(135deg, #60a5fa, #3b82f6)', borderRadius: 22, padding: '22px 22px 20px', marginBottom: 20, boxShadow: '0 8px 24px rgba(59,130,246,0.3)' }}>
            <p style={{ margin: 0, fontSize: 12, color: 'rgba(255,255,255,0.75)', fontWeight: 500 }}>이번 달 추천 지원금</p>
            <p style={{ margin: '6px 0 4px', fontSize: 20, fontWeight: 800, color: '#fff' }}>{featured.title}</p>
            <p style={{ margin: 0, fontSize: 13, color: 'rgba(255,255,255,0.85)' }}>{featured.description} · {featured.deadline}</p>
            <button
              onClick={() => navigate('/category')}
              style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 4, padding: '9px 16px', borderRadius: 12, background: 'rgba(255,255,255,0.22)', color: '#fff', fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer' }}
            >
              자세히 보기 <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* 서비스 메뉴 */}
        <div style={{ background: '#fff', borderRadius: 20, padding: '18px 16px', marginBottom: 20, boxShadow: '0 2px 12px rgba(0,0,0,0.05)' }}>
          <p style={{ margin: '0 0 14px', fontSize: 16, fontWeight: 700, color: '#111' }}>서비스 메뉴</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
            {MENU.map(({ label, path, Icon }) => (
              <button
                key={label}
                onClick={() => navigate(path)}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, padding: '16px 8px', borderRadius: 16, background: '#f8f9ff', border: 'none', cursor: 'pointer' }}
              >
                <div style={{ width: 44, height: 44, borderRadius: 14, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={22} color="#3b82f6" strokeWidth={1.8} />
                </div>
                <span style={{ fontSize: 12, color: '#444', fontWeight: 500 }}>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 인기 지원금 */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#111' }}>인기 지원금</p>
            <button onClick={() => navigate('/category')} style={{ fontSize: 13, color: '#aaa', background: 'none', border: 'none', cursor: 'pointer' }}>전체보기</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {loading ? (
              <div style={{ background: '#fff', borderRadius: 16, padding: 20, textAlign: 'center', fontSize: 13, color: '#aaa' }}>불러오는 중...</div>
            ) : (
              benefits.map((item) => {
                const tag = TAG_COLOR[item.tag] || { bg: '#f3f4f6', color: '#9ca3af' };
                return (
                  <div key={item.id} style={{ background: '#fff', borderRadius: 16, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
                    <span style={{ display: 'inline-block', padding: '3px 9px', borderRadius: 8, fontSize: 11, fontWeight: 700, background: tag.bg, color: tag.color }}>{item.tag}</span>
                    <p style={{ margin: '8px 0 2px', fontSize: 15, fontWeight: 700, color: '#111' }}>{item.title}</p>
                    <p style={{ margin: 0, fontSize: 12, color: '#aaa' }}>{item.org}</p>
                    <p style={{ margin: '6px 0 0', fontSize: 16, fontWeight: 800, color: '#3b82f6' }}>{item.amount}</p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
