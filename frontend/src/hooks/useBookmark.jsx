import { useState, useEffect, useMemo } from 'react';
import { api } from '../utils/api';

const PALETTE = ['#ef4444', '#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#ec4899', '#14b8a6'];

const pad = (n) => String(n).padStart(2, '0');
const dateKey = (y, m, d) => `${y}-${pad(m)}-${pad(d)}`;

// "20260701 ~ 20260731" -> { start: Date, end: Date }
function parseAplyYmd(str) {
  if (!str) return { start: null, end: null };
  const parts = str.split('~').map((s) => s.trim());
  const toDate = (ymd) => {
    if (!ymd || ymd.length !== 8) return null;
    return new Date(Number(ymd.slice(0, 4)), Number(ymd.slice(4, 6)) - 1, Number(ymd.slice(6, 8)));
  };
  return { start: toDate(parts[0]), end: toDate(parts[1] || parts[0]) };
}

// "2026-07-15" | "2026-07-15 ~ 2026-07-20" | "2026-07" -> Date[] (일 단위 정보가 없으면 빈 배열)
function parseEventDate(str) {
  if (!str) return [];
  const parts = str.split('~').map((s) => s.trim());
  const dates = [];
  for (const p of parts) {
    const m = p.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) dates.push(new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  }
  return dates;
}

// Date를 "M/D" 형식으로 표시한다.
function formatMD(date) {
  if (!date) return '';
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

// 오늘부터 target까지 남은 일수를 계산한다(음수면 이미 지남).
function dDay(target) {
  if (!target) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const t = new Date(target);
  t.setHours(0, 0, 0, 0);
  return Math.round((t - today) / (1000 * 60 * 60 * 24));
}

// 즐겨찾기 캘린더 화면의 데이터를 관리한다: 서버에서 즐겨찾기+일정을 불러와 월별로
// 보여줄 색상/D-day를 계산하고, 날짜별 표시 점(dotsByDate)과 범례(legend)를 만든다.
export default function useBookmark() {
  const [rawItems, setRawItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cursor, setCursor] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() }; // month: 0-indexed
  });

  useEffect(() => {
    api.get('/bookmarks/me/calendar')
      .then((data) => setRawItems(data || []))
      .catch(() => setRawItems([]))
      .finally(() => setLoading(false));
  }, []);

  const items = useMemo(() => {
    return rawItems.map((item, i) => {
      const color = PALETTE[i % PALETTE.length];
      const { end: aplyEnd } = parseAplyYmd(item.aplyYmd);
      return { ...item, color, aplyEnd, dday: dDay(aplyEnd) };
    });
  }, [rawItems]);

  // 날짜별( "YYYY-MM-DD" ) -> [{ color, policyId, policyName, label, rawText, dateStr }]
  const dotsByDate = useMemo(() => {
    const map = {};
    const addDot = (date, entry) => {
      if (!date) return;
      const key = dateKey(date.getFullYear(), date.getMonth() + 1, date.getDate());
      if (!map[key]) map[key] = [];
      if (!map[key].some((d) => d.policyId === entry.policyId && d.label === entry.label)) {
        map[key].push(entry);
      }
    };

    items.forEach((item) => {
      if (!item.policy_id) return; // 지역 프로그램 즐겨찾기는 달력에 표시하지 않음
      if (item.aplyEnd) {
        addDot(item.aplyEnd, {
          color: item.color, policyId: item.policy_id, policyName: item.plcyNm,
          label: '신청마감', rawText: null, dateStr: item.aplyYmd,
        });
      }
      (item.events || []).forEach((e) => {
        parseEventDate(e.event_date).forEach((d) => addDot(d, {
          color: item.color, policyId: item.policy_id, policyName: item.plcyNm,
          label: e.event_type, rawText: e.raw_text, dateStr: e.event_date,
        }));
      });
    });

    return map;
  }, [items]);

  const legend = useMemo(
    () => items
      .filter((item) => item.policy_id)
      .map((item) => ({ policyId: item.policy_id, color: item.color, name: item.plcyNm })),
    [items]
  );

  const goPrevMonth = () => {
    setCursor((prev) => (prev.month === 0 ? { year: prev.year - 1, month: 11 } : { year: prev.year, month: prev.month - 1 }));
  };
  const goNextMonth = () => {
    setCursor((prev) => (prev.month === 11 ? { year: prev.year + 1, month: 0 } : { year: prev.year, month: prev.month + 1 }));
  };

  const removeBookmark = async (bookmarkId) => {
    try {
      await api.delete(`/bookmarks/${bookmarkId}`);
      setRawItems((prev) => prev.filter((item) => item.bookmark_id !== bookmarkId));
    } catch {
      // 실패 시 조용히 무시
    }
  };

  return { items, loading, cursor, goPrevMonth, goNextMonth, dotsByDate, legend, dateKey, formatMD, removeBookmark };
}
