import { useState, useEffect } from 'react';
import { api } from '../utils/api';

const CATEGORIES = ['전체', '일자리', '주거', '교육', '복지문화', '참여권리', '지역'];

export default function useCategory() {
  const [activeTab, setActiveTab] = useState('전체');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState('');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bookmarks, setBookmarks] = useState(new Set());
  const [bookmarkIds, setBookmarkIds] = useState(new Map()); // policy_id -> bookmark_id

  useEffect(() => {
    api.get('/bookmarks/me')
      .then((data) => {
        const ids = new Map((data || []).map((b) => [b.policy_id, b.bookmark_id]));
        setBookmarkIds(ids);
        setBookmarks(new Set(ids.keys()));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedKeyword(keyword.trim()), 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  useEffect(() => {
    if (activeTab === '지역' && !selectedRegion) {
      setItems([]);
      setLoading(false);
      return;
    }

    let ignore = false;
    setLoading(true);

    const params = new URLSearchParams({ limit: '100' });
    if (activeTab === '지역') {
      params.set('region', selectedRegion);
    } else if (activeTab !== '전체') {
      params.set('lclsf', activeTab);
    }
    if (debouncedKeyword) {
      params.set('keyword', debouncedKeyword);
    }

    api.get(`/policies/?${params.toString()}`)
      .then((data) => {
        if (ignore) return;
        setItems((data || []).map((p) => ({ id: p.policy_id, plcyNm: p.plcyNm, aplyYmd: p.aplyYmd })));
      })
      .catch(() => {
        if (!ignore) setItems([]);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => { ignore = true; };
  }, [activeTab, selectedRegion, debouncedKeyword]);

  const toggleBookmark = async (id) => {
    const isBookmarked = bookmarks.has(id);
    setBookmarks((prev) => {
      const next = new Set(prev);
      isBookmarked ? next.delete(id) : next.add(id);
      return next;
    });

    try {
      if (isBookmarked) {
        const bookmarkId = bookmarkIds.get(id);
        if (bookmarkId) await api.delete(`/bookmarks/${bookmarkId}`);
        setBookmarkIds((prev) => {
          const next = new Map(prev);
          next.delete(id);
          return next;
        });
      } else {
        const created = await api.post('/bookmarks/', { policy_id: id });
        setBookmarkIds((prev) => new Map(prev).set(id, created.bookmark_id));
      }
    } catch {
      // 실패 시 낙관적 업데이트 되돌리기
      setBookmarks((prev) => {
        const next = new Set(prev);
        isBookmarked ? next.add(id) : next.delete(id);
        return next;
      });
    }
  };

  return {
    categories: CATEGORIES,
    activeTab,
    setActiveTab,
    selectedRegion,
    setSelectedRegion,
    keyword,
    setKeyword,
    items,
    loading,
    bookmarks,
    toggleBookmark,
  };
}
