import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Search, X, Sparkles, ChevronDown, ChevronUp, Bookmark, ExternalLink, Scale } from 'lucide-react';
import useBookmark from '../../hooks/useBookmark';
import usePolicyDetail from '../../hooks/usePolicyDetail';
import { api } from '../../utils/api';
import Modal from '../../Components/Modal';
import PolicyDetailModal from '../../Components/PolicyDetailModal';

function getApplyPeriodText(p) {
  if (p.apply_period_type === '상시') return '상시';
  if (p.apply_period) return p.apply_period;
  if (p.aplyYmd) return p.aplyYmd;
  return null;
}

const COMPARE_ROWS = [
  { label: '지원대상', getValue: (p) => p.ptcpPrpTrgtCn },
  { label: '신청기간', getValue: getApplyPeriodText },
  { label: '지원내용', getValue: (p) => p.plcySprtCn, clamp: true },
  { label: '신청방법', getValue: (p) => p.plcyAplyMthdCn },
];

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토'];
const MONTH_NAMES = Array.from({ length: 12 }, (_, i) => i + 1);

function buildCalendarCells(year, month) {
  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < firstDay.getDay(); i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

function BookmarkItemCard({ item, onRemove, onOpen, comparisonMode, isChecked, onToggleCheck }) {
  const isPolicy = !!item.policy_id;
  const handleCardClick = () => {
    if (!isPolicy) return;
    if (comparisonMode) {
      onToggleCheck(item.policy_id);
    } else {
      onOpen(item);
    }
  };

  return (
    <div
      onClick={isPolicy ? handleCardClick : undefined}
      style={{
        backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
        cursor: isPolicy ? 'pointer' : 'default',
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {comparisonMode && isPolicy ? (
            <input
              type="checkbox"
              checked={isChecked}
              onChange={() => onToggleCheck(item.policy_id)}
              onClick={(e) => e.stopPropagation()}
              style={{ width: 15, height: 15, flexShrink: 0, cursor: 'pointer' }}
            />
          ) : (
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: item.color, flexShrink: 0 }} />
          )}
          <p className="text-[14px] font-bold text-gray-900">{item.plcyNm}</p>
        </div>
        <div className="flex items-center gap-2" style={{ flexShrink: 0 }}>
          {item.dday !== null && (
            <span
              className="text-[11px] font-bold"
              style={{
                padding: '3px 9px', borderRadius: 999,
                backgroundColor: item.dday <= 3 ? '#fee2e2' : '#eff6ff',
                color: item.dday <= 3 ? '#ef4444' : '#3b82f6',
              }}
            >
              {item.dday >= 0 ? `D-${item.dday}` : '마감'}
            </span>
          )}
          <button
            onClick={(e) => { e.stopPropagation(); onRemove(item.bookmark_id); }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex' }}
          >
            <Bookmark size={18} color="#3b82f6" fill="#3b82f6" />
          </button>
        </div>
      </div>
      <p className="mt-1 text-[12px] text-gray-400" style={{ marginLeft: 16 }}>
        {item.sprvsnInstCdNm ? `${item.sprvsnInstCdNm} · ` : ''}
        {item.aplyEnd ? `신청마감 ${item.aplyEnd.getMonth() + 1}/${item.aplyEnd.getDate()}` : '신청기간 정보 없음'}
      </p>
      {item.prep_tip && (
        <div className="flex items-start gap-1.5" style={{ marginTop: 8, marginLeft: 16, padding: '8px 10px', borderRadius: 10, backgroundColor: '#f8f9ff' }}>
          <Sparkles size={13} color="#3b82f6" style={{ marginTop: 1, flexShrink: 0 }} />
          <p className="text-[11px] text-blue-500 font-medium">AI 준비: {item.prep_tip}</p>
        </div>
      )}
      {item.applyUrl && (
        <a
          href={item.applyUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="flex items-center gap-1"
          style={{ marginTop: 8, marginLeft: 16, fontSize: 12, fontWeight: 600, color: '#3b82f6', textDecoration: 'none' }}
        >
          신청 페이지로 이동 <ExternalLink size={12} />
        </a>
      )}
    </div>
  );
}

export default function BookmarkPage() {
  const navigate = useNavigate();
  const { items, loading, cursor, goPrevMonth, goNextMonth, dotsByDate, legend, dateKey, removeBookmark } = useBookmark();
  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();
  const [searchOpen, setSearchOpen] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [selectedDate, setSelectedDate] = useState(null); // "YYYY-MM-DD" | null
  const [hideExpired, setHideExpired] = useState(false);
  const [expiredOpen, setExpiredOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState('all'); // 'all' | 'policy' | 'local_program'
  const legendScrollRef = useRef(null);
  const [activeLegendPage, setActiveLegendPage] = useState(0);
  const pageScrollRef = useRef(null);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [compareItems, setCompareItems] = useState(null); // 비교 모달에 띄울 정책 상세 배열 | null
  const [compareLoading, setCompareLoading] = useState(false);

  const MAX_COMPARE = 3;

  const handleToggleComparisonMode = () => {
    if (comparisonMode) {
      setComparisonMode(false);
      setSelectedForCompare([]);
    } else {
      setComparisonMode(true);
      setTypeFilter('policy');
      setSelectedForCompare([]);
    }
  };

  const handleToggleCompareCheck = (policyId) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(policyId)) return prev.filter((id) => id !== policyId);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, policyId];
    });
  };

  const handleStartCompare = async () => {
    setCompareLoading(true);
    try {
      const results = await Promise.all(
        selectedForCompare.map((id) => api.get(`/policies/${id}`))
      );
      setCompareItems(results);
    } catch {
      setCompareItems([]);
    } finally {
      setCompareLoading(false);
    }
  };

  const closeCompareModal = () => setCompareItems(null);

  const handlePageScroll = (e) => {
    setShowScrollTop(e.target.scrollTop > 200);
  };

  const scrollToTop = () => {
    pageScrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLegendScroll = () => {
    const el = legendScrollRef.current;
    if (!el || el.clientWidth === 0) return;
    setActiveLegendPage(Math.round(el.scrollLeft / el.clientWidth));
  };

  const cells = buildCalendarCells(cursor.year, cursor.month);
  const selectedDots = selectedDate ? (dotsByDate[selectedDate] || []) : [];
  const legendPages = [];
  for (let i = 0; i < legend.length; i += 10) {
    legendPages.push(legend.slice(i, i + 7));
  }
  const isExpired = (item) => item.dday !== null && item.dday < 0;
  const matchesType = (item) => {
    if (typeFilter === 'policy') return !!item.policy_id;
    if (typeFilter === 'local_program') return !!item.local_program_id;
    return true;
  };
  const searchedItems = items
    .filter((item) => !keyword.trim() || item.plcyNm.includes(keyword.trim()))
    .filter(matchesType);
  const activeItems = searchedItems.filter((item) => !isExpired(item));
  const expiredItems = searchedItems.filter(isExpired);

  const handleOpenPolicy = (item) => openPolicy(item.policy_id, item.plcyNm, true);

  const handleOpenPolicyFromCompare = (p) => {
    setCompareItems(null);
    openPolicy(p.policy_id, p.plcyNm, true);
  };

  const handleUnbookmarkFromModal = () => {
    const matched = items.find((item) => item.policy_id === selectedPolicy?.policy_id);
    if (matched) removeBookmark(matched.bookmark_id);
    closePolicy();
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="flex-1 text-[20px] font-bold text-gray-900">즐겨찾기</p>
        <button onClick={() => setSearchOpen((v) => !v)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <Search size={20} color="#555" />
        </button>
      </div>

      <div ref={pageScrollRef} onScroll={handlePageScroll} style={{ flex: 1, overflowY: 'auto' }}>

      {searchOpen && (
        <div className="bg-white" style={{ padding: '0 20px 16px', position: 'relative' }}>
          <input
            autoFocus
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="즐겨찾기한 정책 검색"
            style={{
              width: '100%', padding: '10px 34px 10px 14px', borderRadius: 12,
              border: '1px solid #e5e7eb', fontSize: 13, backgroundColor: '#f9fafb',
              boxSizing: 'border-box',
            }}
          />
          {keyword && (
            <button onClick={() => setKeyword('')} className="bg-transparent border-none cursor-pointer p-0"
              style={{ position: 'absolute', right: 32, top: '50%', transform: 'translateY(-50%)' }}>
              <X size={16} color="#9ca3af" />
            </button>
          )}
        </div>
      )}

      <div style={{ padding: '18px 20px 24px' }}>
        {/* 캘린더 카드 */}
        <div style={{ backgroundColor: '#fff', borderRadius: 20, padding: '18px 16px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
          <div className="flex items-center justify-between" style={{ marginBottom: 14 }}>
            <button onClick={goPrevMonth} className="bg-transparent border-none cursor-pointer p-1">
              <ChevronLeft size={18} color="#9ca3af" />
            </button>
            <p className="text-[15px] font-bold text-gray-900">{cursor.year}년 {MONTH_NAMES[cursor.month]}월</p>
            <button onClick={goNextMonth} className="bg-transparent border-none cursor-pointer p-1">
              <ChevronRight size={18} color="#9ca3af" />
            </button>
          </div>

          <div className="grid grid-cols-7" style={{ marginBottom: 4 }}>
            {WEEKDAYS.map((w) => (
              <div key={w} className="text-center text-[11px] font-semibold text-gray-400" style={{ padding: '4px 0' }}>{w}</div>
            ))}
          </div>

          <div className="grid grid-cols-7">
            {cells.map((day, i) => {
              const key = day ? dateKey(cursor.year, cursor.month + 1, day) : `blank-${i}`;
              const dots = day ? (dotsByDate[key] || []) : [];
              const isToday = day
                && cursor.year === new Date().getFullYear()
                && cursor.month === new Date().getMonth()
                && day === new Date().getDate();
              return (
                <button
                  key={key}
                  onClick={() => dots.length > 0 && setSelectedDate(key)}
                  disabled={dots.length === 0}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '6px 0', minHeight: 40,
                    background: 'transparent', border: 'none', cursor: dots.length > 0 ? 'pointer' : 'default',
                  }}
                >
                  {day && (
                    <>
                      <span
                        className="text-[12px]"
                        style={{
                          width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center',
                          borderRadius: '50%',
                          backgroundColor: isToday ? '#3b82f6' : 'transparent',
                          color: isToday ? '#fff' : '#374151',
                          fontWeight: isToday ? 700 : 500,
                        }}
                      >
                        {day}
                      </span>
                      <div style={{ display: 'flex', gap: 2, marginTop: 3, height: 5 }}>
                        {dots.slice(0, 3).map((d) => (
                          <span key={`${d.policyId}-${d.label}`} style={{ width: 5, height: 5, borderRadius: '50%', backgroundColor: d.color }} />
                        ))}
                      </div>
                    </>
                  )}
                </button>
              );
            })}
          </div>

          {legend.length > 0 && (
            <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid #f3f4f6' }}>
              <div
                ref={legendScrollRef}
                onScroll={handleLegendScroll}
                className="flex overflow-x-auto no-scrollbar"
                style={{ scrollSnapType: 'x mandatory' }}
              >
                {legendPages.map((page, pageIndex) => (
                  <div
                    key={pageIndex}
                    className="flex flex-col"
                    style={{ flex: '0 0 100%', scrollSnapAlign: 'start', gap: 8, boxSizing: 'border-box' }}
                  >
                    {page.map((l) => (
                      <div key={l.policyId} className="flex items-center gap-1.5">
                        <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: l.color, flexShrink: 0 }} />
                        <span className="text-[11px] text-gray-500 font-medium">{l.name}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              {legendPages.length > 1 && (
                <div className="flex justify-center items-center gap-1.5" style={{ marginTop: 10 }}>
                  {legendPages.map((_, i) => (
                    <span
                      key={i}
                      style={{
                        width: i === activeLegendPage ? 16 : 6, height: 6, borderRadius: 999,
                        backgroundColor: i === activeLegendPage ? '#3b82f6' : '#e5e7eb',
                        transition: 'all 0.2s',
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 즐겨찾기 일정 리스트 */}
        <div style={{ margin: '20px 0 12px' }}>
          <p className="text-[15px] font-bold text-gray-900">즐겨찾기 일정 {items.length}</p>
          <div className="flex items-center flex-wrap" style={{ gap: 8, marginTop: 8 }}>
            <button
              onClick={() => setHideExpired((v) => !v)}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '6px 10px', borderRadius: 999, border: 'none', cursor: 'pointer',
                backgroundColor: hideExpired ? '#3b82f6' : '#fff',
                color: hideExpired ? '#fff' : '#6b7280',
                fontSize: 12, fontWeight: 700,
                boxShadow: hideExpired ? 'none' : '0 1px 4px rgba(0,0,0,0.08)',
              }}
            >
              마감공고 제외
            </button>

            <div style={{ display: 'flex', borderRadius: 999, backgroundColor: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
              {[
                { value: 'all', label: '전체' },
                { value: 'policy', label: '정책' },
                { value: 'local_program', label: '지역프로그램' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setTypeFilter(opt.value)}
                  style={{
                    padding: '6px 12px', border: 'none', cursor: 'pointer',
                    backgroundColor: typeFilter === opt.value ? '#3b82f6' : 'transparent',
                    color: typeFilter === opt.value ? '#fff' : '#6b7280',
                    fontSize: 12, fontWeight: 700,
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <button
              onClick={handleToggleComparisonMode}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '6px 10px', borderRadius: 999, border: 'none', cursor: 'pointer',
                backgroundColor: comparisonMode ? '#3b82f6' : '#fff',
                color: comparisonMode ? '#fff' : '#6b7280',
                fontSize: 12, fontWeight: 700,
                boxShadow: comparisonMode ? 'none' : '0 1px 4px rgba(0,0,0,0.08)',
              }}
            >
              <Scale size={13} />
              {comparisonMode ? '취소' : '비교하기'}
            </button>
          </div>

          {comparisonMode && (
            <button
              onClick={handleStartCompare}
              disabled={selectedForCompare.length < 2 || compareLoading}
              style={{
                marginTop: 8, width: '100%', padding: '10px', borderRadius: 12, border: 'none',
                backgroundColor: selectedForCompare.length >= 2 ? '#3b82f6' : '#e5e7eb',
                color: selectedForCompare.length >= 2 ? '#fff' : '#9ca3af',
                fontSize: 13, fontWeight: 700,
                cursor: selectedForCompare.length >= 2 ? 'pointer' : 'default',
              }}
            >
              {compareLoading ? '불러오는 중...' : `선택한 ${selectedForCompare.length}개 비교하기`}
            </button>
          )}
        </div>

        <div className="flex flex-col gap-2.5">
          {loading ? (
            <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>불러오는 중...</div>
          ) : searchedItems.length === 0 ? (
            <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>
              {items.length === 0 ? '즐겨찾기한 정책이 없어요. 전체보기에서 관심있는 정책을 즐겨찾기 해보세요.' : `'${keyword}'와 일치하는 즐겨찾기가 없어요.`}
            </div>
          ) : (
            <>
              {activeItems.map((item) => (
                <BookmarkItemCard
                  key={item.bookmark_id}
                  item={item}
                  onRemove={removeBookmark}
                  onOpen={handleOpenPolicy}
                  comparisonMode={comparisonMode}
                  isChecked={selectedForCompare.includes(item.policy_id)}
                  onToggleCheck={handleToggleCompareCheck}
                />
              ))}

              {!hideExpired && expiredItems.length > 0 && (
                <div>
                  <button
                    onClick={() => setExpiredOpen((v) => !v)}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '10px 14px', borderRadius: 999, border: 'none', cursor: 'pointer',
                      backgroundColor: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                    }}
                  >
                    <span className="text-[13px] font-semibold text-gray-500">마감된 공고 {expiredItems.length}건</span>
                    {expiredOpen ? <ChevronUp size={16} color="#9ca3af" /> : <ChevronDown size={16} color="#9ca3af" />}
                  </button>

                  {expiredOpen && (
                    <div className="flex flex-col gap-2.5">
                      {expiredItems.map((item) => (
                        <BookmarkItemCard
                  key={item.bookmark_id}
                  item={item}
                  onRemove={removeBookmark}
                  onOpen={handleOpenPolicy}
                  comparisonMode={comparisonMode}
                  isChecked={selectedForCompare.includes(item.policy_id)}
                  onToggleCheck={handleToggleCompareCheck}
                />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
      </div>

      {showScrollTop && (
        <button
          onClick={scrollToTop}
          style={{
            position: 'absolute', right: 20, bottom: 20, width: 44, height: 44,
            borderRadius: '50%', border: 'none', backgroundColor: '#3b82f6', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(59,130,246,0.4)',
          }}
        >
          <ChevronUp size={22} />
        </button>
      )}

      <Modal
        isOpen={!!selectedDate}
        onClose={() => setSelectedDate(null)}
        title={selectedDate ? `${Number(selectedDate.split('-')[1])}월 ${Number(selectedDate.split('-')[2])}일 일정` : ''}
      >
        <div className="flex flex-col gap-3">
          {selectedDots.map((d) => (
            <div key={`${d.policyId}-${d.label}`} style={{ padding: '12px 14px', borderRadius: 14, backgroundColor: '#f8f9ff', borderLeft: `4px solid ${d.color}` }}>
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-bold text-gray-900">{d.policyName}</span>
                <span
                  className="text-[11px] font-bold"
                  style={{ padding: '2px 8px', borderRadius: 999, backgroundColor: `${d.color}22`, color: d.color }}
                >
                  {d.label}
                </span>
              </div>
              {d.rawText && <p className="mt-1.5 text-[12px] text-gray-500">"{d.rawText}"</p>}
              {d.dateStr && <p className="mt-1 text-[11px] text-gray-400">{d.dateStr}</p>}
            </div>
          ))}
        </div>
      </Modal>

      <PolicyDetailModal
        selectedPolicy={selectedPolicy}
        policyLoading={policyLoading}
        isBookmarked={true}
        onToggleBookmark={handleUnbookmarkFromModal}
        onClose={closePolicy}
      />

      <Modal isOpen={!!compareItems} onClose={closeCompareModal} title="정책 비교">
        {compareItems && compareItems.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <div style={{ display: 'flex', gap: 12, minWidth: compareItems.length * 220 }}>
              {compareItems.map((p, i) => (
                <div
                  key={p.policy_id}
                  style={{
                    flex: '0 0 220px', display: 'flex', flexDirection: 'column', gap: 12,
                    borderLeft: i > 0 ? '1px solid #f3f4f6' : 'none', paddingLeft: i > 0 ? 12 : 0,
                  }}
                >
                  <p className="text-[13px] font-bold text-gray-900" style={{ minHeight: 34, margin: 0 }}>{p.plcyNm}</p>
                  {COMPARE_ROWS.map((row) => (
                    <div key={row.label}>
                      <p className="text-[11px] font-semibold text-blue-500" style={{ margin: '0 0 2px' }}>{row.label}</p>
                      <p
                        className="text-[12px] text-gray-600"
                        style={{
                          margin: 0, lineHeight: 1.5, whiteSpace: 'pre-line',
                          ...(row.clamp ? { display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' } : {}),
                        }}
                      >
                        {row.getValue(p) || '정보 없음'}
                      </p>
                    </div>
                  ))}
                  <button
                    onClick={() => handleOpenPolicyFromCompare(p)}
                    className="flex items-center gap-1"
                    style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', fontSize: 12, fontWeight: 600, color: '#3b82f6' }}
                  >
                    자세히 보기 <ExternalLink size={11} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
