import { useNavigate } from 'react-router-dom';
import { Bell, RefreshCw, List, Sparkles, FileText, ScanSearch, BellRing, Bookmark, ChevronRight } from 'lucide-react';
import useHome from '../../hooks/useHome';

const MENU = [
  { label: '전체보기', path: '/category', Icon: List },
  { label: '맞춤추천', path: '/recommendation', Icon: Sparkles },
  { label: '공고요약', path: '/summary', Icon: FileText },
  { label: '사진분석', path: '/ocr', Icon: ScanSearch },
  { label: '지원금알림', path: '/notification', Icon: BellRing },
  { label: '즐겨찾기', path: '/bookmark', Icon: Bookmark },
];

export default function HomePage() {
  const { benefits, featured, loading, userName } = useHome();
  const navigate = useNavigate();

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      {/* 헤더 */}
      <div className="flex justify-between items-start bg-white" style={{ padding: '20px 20px 16px' }}>
        <div>
          <p className="text-[13px] text-gray-400">안녕하세요</p>
          <p className="mt-0.5 text-[22px] font-extrabold text-gray-900">{userName}님 👋</p>
        </div>
        <div className="flex gap-2 mt-1">
          {[Bell, RefreshCw].map((Icon, i) => (
            <button key={i} className="w-[38px] h-[38px] rounded-full border border-gray-100 bg-white flex items-center justify-center cursor-pointer">
              <Icon size={i === 0 ? 18 : 16} color="#555" />
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '16px 20px 24px' }}>
        {/* 배너 */}
        {featured && (
          <div
            style={{
              background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
              borderRadius: 22,
              padding: 22,
              marginBottom: 16,
              boxShadow: '0 8px 24px rgba(59,130,246,0.30)',
            }}
          >
            <p className="text-[12px] text-white/75 font-medium">이번 달 추천 지원금</p>
            <p className="mt-1.5 mb-1 text-[20px] font-extrabold text-white">{featured.title}</p>
            <p className="text-[13px] text-white/85">{featured.description} · {featured.deadline}</p>
            <button
              onClick={() => navigate('/category')}
              className="mt-4 flex items-center gap-1 text-white text-[13px] font-semibold cursor-pointer"
              style={{ padding: '8px 16px', borderRadius: 12, background: 'rgba(255,255,255,0.2)', border: 'none' }}
            >
              자세히 보기 <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* 서비스 메뉴 */}
        <div
          style={{
            backgroundColor: '#fff',
            borderRadius: 20,
            padding: '18px 18px',
            marginBottom: 16,
            boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
          }}
        >
          <p className="mb-3.5 text-[16px] font-bold text-gray-900">서비스 메뉴</p>
          <div className="grid grid-cols-3 gap-2.5">
            {MENU.map(({ label, path, Icon }) => (
              <button
                key={label}
                onClick={() => navigate(path)}
                className="flex flex-col items-center gap-2 cursor-pointer"
                style={{ padding: '14px 8px', borderRadius: 16, backgroundColor: '#f8f9ff', border: 'none' }}
              >
                <div className="w-11 h-11 rounded-[14px] bg-blue-50 flex items-center justify-center">
                  <Icon size={22} color="#3b82f6" strokeWidth={1.8} />
                </div>
                <span className="text-[12px] text-gray-600 font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 인기 지원금 */}
        <div className="flex justify-between items-center mb-3">
          <p className="text-[16px] font-bold text-gray-900">인기 지원금</p>
          <button onClick={() => navigate('/category')} className="text-[13px] text-gray-400 bg-transparent border-none cursor-pointer">
            전체보기
          </button>
        </div>
        <div className="flex flex-col gap-2.5">
          {loading ? (
            <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 20, textAlign: 'center', fontSize: 13, color: '#9ca3af', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>불러오는 중...</div>
          ) : benefits.map((item) => (
            <div key={item.id} style={{ backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
              <p className="text-[15px] font-bold text-gray-900">{item.plcyNm}</p>
              <p className="mt-1 text-[12px] text-gray-400">{item.aplyYmd}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
