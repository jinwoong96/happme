import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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

const CONSONANT_GROUPS = ['전체', 'ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ', '기타'];

// IME로 한글을 조합하는 중에는 "ㄱ", "ㅓ"처럼 완성되지 않은 낱자(호환용 자모, U+3131~U+318E)가
// 마지막 글자로 잠깐 나타난다. 이 상태로 검색을 보내면 실제 정책명과 매칭될 일이 거의 없어서
// 결과가 없거나 엉뚱하게 필터링된 것처럼 보이므로, 이 경우엔 API 호출을 건너뛴다.
function endsWithIncompleteJamo(text) {
  if (!text) return false;
  const code = text.charCodeAt(text.length - 1);
  return code >= 0x3131 && code <= 0x318e;
}

export default function useCategory() {
  const location = useLocation();
  // 홈 화면 "많이 찾는 정책 > 전체보기"처럼 특정 정렬로 들어오길 원하는 진입 경로를 위한 기본값.
  const initialSort = SORT_OPTIONS.some((o) => o.value === location.state?.sort) ? location.state.sort : 'none';

  const [activeTab, setActiveTab] = useState('전체');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState('');
  const [sortOption, setSortOption] = useState(initialSort);
  const [includeClosed, setIncludeClosed] = useState(false);
  const [consonant, setConsonant] = useState('전체');
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
    const timer = setTimeout(() => {
      const trimmed = keyword.trim();
      if (!endsWithIncompleteJamo(trimmed)) {
        setDebouncedKeyword(trimmed);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [keyword]);

  // 마감임박순에서는 "마감된 정책 보기" 체크박스를 숨기므로, 안 보이는 상태로 값만 남지 않게 초기화한다.
  useEffect(() => {
    if (sortOption === 'deadline') setIncludeClosed(false);
  }, [sortOption]);

  // 초성 선택은 가나다순일 때만 보이므로, 다른 정렬로 바뀌면 숨겨진 채로 값만 남지 않게 초기화한다.
  useEffect(() => {
    if (sortOption !== 'alpha') setConsonant('전체');
  }, [sortOption]);

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
    if (includeClosed) {
      params.set('include_closed', 'true');
    }
    if (sortOption === 'alpha' && consonant !== '전체') {
      params.set('consonant', consonant);
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
  }, [activeTab, selectedRegion, debouncedKeyword, sortOption, includeClosed, consonant]);

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
    includeClosed,
    setIncludeClosed,
    consonantGroups: CONSONANT_GROUPS,
    consonant,
    setConsonant,
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
