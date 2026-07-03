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

function formatMD(date) {
  if (!date) return '';
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function dDay(target) {
  if (!target) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const t = new Date(target);
  t.setHours(0, 0, 0, 0);
  return Math.round((t - today) / (1000 * 60 * 60 * 24));
}

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

  // 날짜별( "YYYY-MM-DD" ) -> [{ color, policyId, label }]
  const dotsByDate = useMemo(() => {
    const map = {};
    const addDot = (date, color, policyId, label) => {
      if (!date) return;
      const key = dateKey(date.getFullYear(), date.getMonth() + 1, date.getDate());
      if (!map[key]) map[key] = [];
      if (!map[key].some((d) => d.policyId === policyId)) {
        map[key].push({ color, policyId, label });
      }
    };

    items.forEach((item) => {
      if (item.aplyEnd) addDot(item.aplyEnd, item.color, item.policy_id, '신청마감');
      (item.events || []).forEach((e) => {
        parseEventDate(e.event_date).forEach((d) => addDot(d, item.color, item.policy_id, e.event_type));
      });
    });

    return map;
  }, [items]);

  const legend = useMemo(
    () => items.map((item) => ({ policyId: item.policy_id, color: item.color, name: item.plcyNm })),
    [items]
  );

  const goPrevMonth = () => {
    setCursor((prev) => (prev.month === 0 ? { year: prev.year - 1, month: 11 } : { year: prev.year, month: prev.month - 1 }));
  };
  const goNextMonth = () => {
    setCursor((prev) => (prev.month === 11 ? { year: prev.year + 1, month: 0 } : { year: prev.year, month: prev.month + 1 }));
  };

  return { items, loading, cursor, goPrevMonth, goNextMonth, dotsByDate, legend, dateKey, formatMD };
}
