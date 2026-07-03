import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Search, X, Sparkles } from 'lucide-react';
import useBookmark from '../../hooks/useBookmark';
import Modal from '../../Components/Modal';

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

export default function BookmarkPage() {
  const navigate = useNavigate();
  const { items, loading, cursor, goPrevMonth, goNextMonth, dotsByDate, legend, dateKey } = useBookmark();
  const [searchOpen, setSearchOpen] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [selectedDate, setSelectedDate] = useState(null); // "YYYY-MM-DD" | null

  const cells = buildCalendarCells(cursor.year, cursor.month);
  const selectedDots = selectedDate ? (dotsByDate[selectedDate] || []) : [];
  const filteredItems = keyword.trim()
    ? items.filter((item) => item.plcyNm.includes(keyword.trim()))
    : items;

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="flex-1 text-[18px] font-bold text-gray-900">내 지원금 캘린더</p>
        <button onClick={() => setSearchOpen((v) => !v)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <Search size={20} color="#555" />
        </button>
      </div>

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
            <div className="flex flex-wrap items-center" style={{ gap: '6px 14px', marginTop: 14, paddingTop: 14, borderTop: '1px solid #f3f4f6' }}>
              {legend.map((l) => (
                <div key={l.policyId} className="flex items-center gap-1.5">
                  <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: l.color, flexShrink: 0 }} />
                  <span className="text-[11px] text-gray-500 font-medium">{l.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 즐겨찾기 일정 리스트 */}
        <div className="flex items-center justify-between" style={{ margin: '20px 0 12px' }}>
          <p className="text-[15px] font-bold text-gray-900">즐겨찾기 일정 {items.length}</p>
        </div>

        <div className="flex flex-col gap-2.5">
          {loading ? (
            <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>불러오는 중...</div>
          ) : filteredItems.length === 0 ? (
            <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>
              {items.length === 0 ? '즐겨찾기한 정책이 없어요. 전체보기에서 관심있는 정책을 즐겨찾기 해보세요.' : `'${keyword}'와 일치하는 즐겨찾기가 없어요.`}
            </div>
          ) : filteredItems.map((item) => (
            <div key={item.bookmark_id} style={{ backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: item.color, flexShrink: 0 }} />
                  <p className="text-[14px] font-bold text-gray-900">{item.plcyNm}</p>
                </div>
                {item.dday !== null && (
                  <span
                    className="text-[11px] font-bold"
                    style={{
                      padding: '3px 9px', borderRadius: 999, flexShrink: 0,
                      backgroundColor: item.dday <= 3 ? '#fee2e2' : '#eff6ff',
                      color: item.dday <= 3 ? '#ef4444' : '#3b82f6',
                    }}
                  >
                    {item.dday >= 0 ? `D-${item.dday}` : '마감'}
                  </span>
                )}
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
            </div>
          ))}
        </div>
      </div>

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
    </div>
  );
}
