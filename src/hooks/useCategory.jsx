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

  const toggleBookmark = (id) => {
    setBookmarks((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
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
