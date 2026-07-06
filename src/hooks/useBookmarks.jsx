import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export default function useBookmarks() {
  const [bookmarkMap, setBookmarkMap] = useState({}); // policy_id -> bookmark_id
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    Promise.all([
      api.get('/bookmarks/me').catch(() => []),
      api.get('/users/me').catch(() => null),
    ]).then(([bookmarks, me]) => {
      if (ignore) return;
      const map = {};
      (bookmarks || []).forEach((b) => { map[b.policy_id] = b.bookmark_id; });
      setBookmarkMap(map);
      setUserId(me?.user_id ?? null);
    }).finally(() => {
      if (!ignore) setLoading(false);
    });

    return () => { ignore = true; };
  }, []);

  // bookmarkMap(/bookmarks/me 기준)에 아직 없으면 호출부에서 넘겨준 fallback(추천 응답의 is_bookmarked)을 사용합니다.
  // /bookmarks/me 요청이 끝나기 전 깜빡임을 없애기 위한 용도입니다.
  const isBookmarked = useCallback((policyId, fallback = false) => {
    if (bookmarkMap[policyId] !== undefined) return true;
    if (loading) return Boolean(fallback);
    return false;
  }, [bookmarkMap, loading]);

  const toggleBookmark = useCallback(async (policyId) => {
    const bookmarkId = bookmarkMap[policyId];
    try {
      if (bookmarkId) {
        await api.delete(`/bookmarks/${bookmarkId}`);
        setBookmarkMap((prev) => {
          const next = { ...prev };
          delete next[policyId];
          return next;
        });
      } else {
        if (!userId) return;
        const created = await api.post('/bookmarks/', { user_id: userId, policy_id: policyId });
        setBookmarkMap((prev) => ({ ...prev, [policyId]: created.bookmark_id }));
      }
    } catch {
      // 실패 시 조용히 무시
    }
  }, [bookmarkMap, userId]);

  return { isBookmarked, toggleBookmark, loading };
}
