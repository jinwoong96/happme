import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../utils/api';

// "20260701 ~ 20260731" -> "2026-07-31" (마감일만 표시)
function formatDeadline(aplyYmd) {
  if (!aplyYmd) return '';
  const end = aplyYmd.split('~').pop().trim();
  if (end.length !== 8) return aplyYmd;
  return `${end.slice(0, 4)}-${end.slice(4, 6)}-${end.slice(6, 8)}`;
}

export default function useNotification() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    api.get('/bookmarks/me/calendar')
      .then((data) => {
        if (ignore) return;
        setItems((data || []).map((b) => ({
          id: b.bookmark_id,
          title: b.plcyNm,
          org: b.sprvsnInstCdNm || '',
          deadline: formatDeadline(b.aplyYmd),
          on: b.alarm_yn,
        })));
      })
      .catch(() => { if (!ignore) setItems([]); })
      .finally(() => { if (!ignore) setLoading(false); });

    return () => { ignore = true; };
  }, []);

  const toggle = useCallback((id) => {
    setItems((prev) => prev.map((item) => item.id === id ? { ...item, on: !item.on } : item));

    const target = items.find((item) => item.id === id);
    const nextOn = target ? !target.on : true;
    api.patch(`/bookmarks/${id}`, { alarm_yn: nextOn }).catch(() => {
      // 실패 시 되돌리기
      setItems((prev) => prev.map((item) => item.id === id ? { ...item, on: !item.on } : item));
    });
  }, [items]);

  const filtered = useMemo(() => items.filter((item) =>
    item.title.includes(search) || item.org.includes(search)
  ), [items, search]);

  return { filtered, search, setSearch, toggle, loading, isEmpty: items.length === 0 };
}
