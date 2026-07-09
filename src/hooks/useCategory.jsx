import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import usePolicyDetail from './usePolicyDetail';

const CATEGORIES = ['전체', '일자리', '주거', '교육', '복지문화', '참여권리', '지역'];

const SORT_OPTIONS = [
  { value: 'none', label: '정렬 안함' },
  { value: 'deadline', label: '마감 임박순' },
  { value: 'latest', label: '최신 등록순' },
  { value: 'popular', label: '인기순' },
  { value: 'alpha', label: '가나다순' },
];

export default function useCategory() {
  const [activeTab, setActiveTab] = useState('전체');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState('');
  const [sortOption, setSortOption] = useState('none');
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
    if (sortOption !== 'none') {
      params.set('sort', sortOption);
    }

    api.get(`/policies/?${params.toString()}`)
      .then((data) => {
        if (ignore) return;
        setItems((data || []).map((p) => ({
          policy_id: p.policy_id,
          plcyNo: p.plcyNo,
          policy_name: p.plcyNm,
          aplyYmd: p.aplyYmd,
          policy_summary: p.policy_summary,
          apply_period_type: p.apply_period_type,
          apply_period: p.apply_period,
          target: p.target,
        })));
      })
      .catch(() => {
        if (!ignore) setItems([]);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => { ignore = true; };
  }, [activeTab, selectedRegion, debouncedKeyword, sortOption]);

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

  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();

  return {
    categories: CATEGORIES,
    sortOptions: SORT_OPTIONS,
    activeTab,
    setActiveTab,
    selectedRegion,
    setSelectedRegion,
    keyword,
    setKeyword,
    sortOption,
    setSortOption,
    items,
    loading,
    bookmarks,
    toggleBookmark,
    selectedPolicy,
    policyLoading,
    openPolicy,
    closePolicy,
  };
}
