import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, List, Sparkles, FileText, ScanSearch, BellRing, Bookmark, ChevronRight } from 'lucide-react';
import useHome from '../../hooks/useHome';
import useBookmarks from '../../hooks/useBookmarks';
import PolicyCard from '../../Components/PolicyCard';
import PolicyDetailModal from '../../Components/PolicyDetailModal';

const BANNER_REASON_LABEL = {
  amount: '지원금액 높은 정책',
  deadline: '마감임박',
  latest: '최근 등록',
};

function formatWon(amount) {
  if (amount == null) return null;
  if (amount >= 100_000_000) {
    const eok = amount / 100_000_000;
    return `최대 ${Number.isInteger(eok) ? eok : eok.toFixed(1)}억원 지원`;
  }
  if (amount >= 10_000) {
    return `최대 ${Math.round(amount / 10_000).toLocaleString()}만원 지원`;
  }
  return `최대 ${amount.toLocaleString()}원 지원`;
}

function formatDeadline(aplyEndDt) {
  if (!aplyEndDt) return null;
  const end = new Date(aplyEndDt);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
  return diffDays >= 0 ? `D-${diffDays}` : '마감';
}

// 배너는 지원금액이 있는 정책만 모으므로, 금액을 기본으로 보여주고 마감 여부(상시/D-n)를 덧붙인다.
function getBannerDetail(item) {
  const amountText = item.maxSprtAmt != null ? formatWon(item.maxSprtAmt) : null;
  const deadlineText = item.aplyEndDt ? formatDeadline(item.aplyEndDt) : '상시';
  return amountText ? `${amountText} · ${deadlineText}` : deadlineText;
}

const MENU = [
  { label: '맞춤정책', path: '/recommendation/current', Icon: List },
  { label: '상황매칭', path: '/recommendation', Icon: Sparkles },
  { label: '공고요약', path: '/summary', Icon: FileText },
  { label: '사진분석', path: '/ocr', Icon: ScanSearch },
  { label: '지원금알림', path: '/notification', Icon: BellRing },
  { label: '지역프로그램', path: '/region', Icon: Bookmark },
];

// 홈에서는 신청 가능 여부를 판정하지 않고 정책을 그대로 보여주므로, 상시 여부만 배지로 표시한다.
function getBadge(policy) {
  return policy.apply_period_type === '상시' ? { label: '상시', bg: '#dcfce7', color: '#16a34a' } : null;
}

export default function HomePage() {
  const {
    benefits, banner, bannerLoading, loading, userName, unreadCount,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  } = useHome();
  const { isBookmarked, toggleBookmark, loading: bookmarksLoading } = useBookmarks();
  const navigate = useNavigate();
  const bannerScrollRef = useRef(null);
  const [activeBannerIndex, setActiveBannerIndex] = useState(0);

  const handleBannerScroll = () => {
    const el = bannerScrollRef.current;
    if (!el || el.clientWidth === 0) return;
    setActiveBannerIndex(Math.round(el.scrollLeft / el.clientWidth));
  };

  // 5초마다 자동으로 다음 배너로 슬라이드하고, 마지막이면 처음으로 돌아간다.
  // activeBannerIndex가 바뀔 때마다(자동이든, 사용자가 직접 넘기든) 타이머를 새로 시작한다.
  useEffect(() => {
    if (banner.length <= 1) return;

    const timer = setInterval(() => {
      const el = bannerScrollRef.current;
      if (!el || el.clientWidth === 0) return;

      setActiveBannerIndex((prev) => {
        const next = (prev + 1) % banner.length;
        el.scrollTo({ left: next * el.clientWidth, behavior: 'smooth' });
        return next;
      });
    }, 5000);

    return () => clearInterval(timer);
  }, [banner.length, activeBannerIndex]);

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      {/* 헤더 */}
      <div className="flex justify-between items-start bg-white" style={{ padding: '20px 20px 16px' }}>
        <div>
          <p className="text-[13px] text-gray-400">안녕하세요</p>
          <p className="mt-0.5 text-[22px] font-extrabold text-gray-900">{userName}님 👋</p>
        </div>
        <div className="flex gap-2 mt-1">
          <button
            onClick={() => navigate('/alerts')}
            style={{ position: 'relative' }}
            className="w-[38px] h-[38px] rounded-full border border-gray-100 bg-white flex items-center justify-center cursor-pointer"
          >
            <Bell size={18} color="#555" />
            {unreadCount > 0 && (
              <span
                style={{
                  position: 'absolute', top: 6, right: 6,
                  width: 8, height: 8, borderRadius: '50%',
                  backgroundColor: '#ef4444', border: '1.5px solid #fff',
                }}
              />
            )}
          </button>
        </div>
      </div>

      <div style={{ padding: '16px 20px 24px' }}>
        {/* 배너: 지원금액 높은 순 / 마감임박 / 최신 등록 정책을 옆으로 넘겨가며 보여준다 */}
        {!bannerLoading && banner.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div
              ref={bannerScrollRef}
              onScroll={handleBannerScroll}
              className="flex overflow-x-auto no-scrollbar"
              style={{ scrollSnapType: 'x mandatory' }}
            >
              {banner.map((item) => (
                <div
                  key={item.policy_id}
                  onClick={() => openPolicy(item.policy_id, item.policy_name, isBookmarked(item.policy_id))}
                  style={{
                    flex: '0 0 100%',
                    scrollSnapAlign: 'start',
                    background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
                    borderRadius: 22,
                    padding: 22,
                    boxShadow: '0 8px 24px rgba(59,130,246,0.30)',
                    cursor: 'pointer',
                    boxSizing: 'border-box',
                  }}
                >
                  <span
                    className="text-[11px] font-semibold text-white"
                    style={{ padding: '3px 10px', borderRadius: 999, background: 'rgba(255,255,255,0.25)' }}
                  >
                    {BANNER_REASON_LABEL[item.banner_reason] || '이번 달 추천 정책'}
                  </span>
                  <p className="mt-2 mb-1 text-[18px] font-extrabold text-white line-clamp-1">{item.policy_name}</p>
                  <p className="text-[13px] text-white/85 line-clamp-1">{getBannerDetail(item)}</p>
                  <button
                    onClick={(e) => { e.stopPropagation(); openPolicy(item.policy_id, item.policy_name, isBookmarked(item.policy_id)); }}
                    className="mt-4 flex items-center gap-1 text-white text-[13px] font-semibold cursor-pointer"
                    style={{ padding: '8px 16px', borderRadius: 12, background: 'rgba(255,255,255,0.2)', border: 'none' }}
                  >
                    자세히 보기 <ChevronRight size={14} />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex justify-center items-center gap-1.5" style={{ marginTop: 10 }}>
              {banner.map((_, i) => (
                <span
                  key={i}
                  style={{
                    width: i === activeBannerIndex ? 16 : 6, height: 6, borderRadius: 999,
                    backgroundColor: i === activeBannerIndex ? '#3b82f6' : '#e5e7eb',
                    transition: 'all 0.2s',
                  }}
                />
              ))}
            </div>
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
          <p className="text-[16px] font-bold text-gray-900">많이 찾는 정책</p>
          <button onClick={() => navigate('/category', { state: { sort: 'popular' } })} className="text-[13px] text-gray-400 bg-transparent border-none cursor-pointer">
            전체보기
          </button>
        </div>
        <div className="flex flex-col gap-2.5">
          {loading ? (
            <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 20, textAlign: 'center', fontSize: 13, color: '#9ca3af', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>불러오는 중...</div>
          ) : benefits.map((item) => (
            <PolicyCard
              key={item.policy_id}
              policy={item}
              badge={getBadge(item)}
              onOpen={openPolicy}
              isBookmarked={isBookmarked(item.policy_id)}
              onToggleBookmark={toggleBookmark}
              bookmarkDisabled={bookmarksLoading}
            />
          ))}
        </div>
      </div>

      <PolicyDetailModal
        selectedPolicy={selectedPolicy}
        policyLoading={policyLoading}
        isBookmarked={isBookmarked(selectedPolicy?.policy_id, selectedPolicy?.is_bookmarked)}
        onToggleBookmark={toggleBookmark}
        bookmarkDisabled={bookmarksLoading}
        onClose={closePolicy}
      />
    </div>
  );
}