import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../utils/api';

// "20260701 ~ 20260731" -> "2026-07-31" (마감일만 표시)
function formatDeadline(aplyYmd) {
  if (!aplyYmd) return '';
  const end = aplyYmd.split('~').pop().trim();
  if (end.length !== 8) return aplyYmd;
  return `${end.slice(0, 4)}-${end.slice(4, 6)}-${end.slice(6, 8)}`;
}

// 알림 설정 화면: 즐겨찾기별 마감 알림 on/off, 검색, 공고문 키워드 알림 등록/삭제를 관리한다.
export default function useNotification() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const [keywords, setKeywords] = useState([]);
  const [keywordsLoading, setKeywordsLoading] = useState(true);
  const [keywordError, setKeywordError] = useState('');

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

    api.get('/alert-keywords/me')
      .then((data) => {
        if (!ignore) setKeywords(data || []);
      })
      .catch(() => { if (!ignore) setKeywords([]); })
      .finally(() => { if (!ignore) setKeywordsLoading(false); });

    return () => { ignore = true; };
  }, []);

  // 공고문 알림 받기: 제목이 아니라 "보증금", "전세보증금 관련"처럼 자유 텍스트로 등록.
  // 새 공고문이 생기거나 바뀔 때 이 텍스트 기준으로 내 조건에 맞는지 비교해서 알림을 보내준다.
  const addKeyword = useCallback(async (text) => {
    const keyword = text.trim();
    if (!keyword) return false;
    setKeywordError('');
    try {
      const created = await api.post('/alert-keywords/', { keyword });
      setKeywords((prev) => [created, ...prev]);
      return true;
    } catch (e) {
      setKeywordError(e.message || '키워드 등록에 실패했어요.');
      return false;
    }
  }, []);

  const removeKeyword = useCallback((keywordId) => {
    setKeywords((prev) => prev.filter((k) => k.keyword_id !== keywordId));
    api.delete(`/alert-keywords/${keywordId}`).catch(() => {
      // 실패 시 목록 다시 불러오기
      api.get('/alert-keywords/me').then((data) => setKeywords(data || [])).catch(() => {});
    });
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

  return {
    filtered, search, setSearch, toggle, loading, isEmpty: items.length === 0,
    keywords, keywordsLoading, keywordError, addKeyword, removeKeyword,
  };
}
