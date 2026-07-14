import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export default function useBookmarks() {
  const [bookmarkMap, setBookmarkMap] = useState({}); // policy_id -> bookmark_id
  const [localProgramMap, setLocalProgramMap] = useState({}); // local_program_id -> bookmark_id
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
      const lpMap = {};
      (bookmarks || []).forEach((b) => {
        if (b.policy_id) map[b.policy_id] = b.bookmark_id;
        if (b.local_program_id) lpMap[b.local_program_id] = b.bookmark_id;
      });
      setBookmarkMap(map);
      setLocalProgramMap(lpMap);
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
    if (policyId == null) return;

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

  const isLocalProgramBookmarked = useCallback((localProgramId, fallback = false) => {
    if (localProgramMap[localProgramId] !== undefined) return true;
    if (loading) return Boolean(fallback);
    return false;
  }, [localProgramMap, loading]);

  const toggleLocalProgramBookmark = useCallback(async (localProgramId) => {
    if (localProgramId == null) return;

    const bookmarkId = localProgramMap[localProgramId];
    try {
      if (bookmarkId) {
        await api.delete(`/bookmarks/${bookmarkId}`);
        setLocalProgramMap((prev) => {
          const next = { ...prev };
          delete next[localProgramId];
          return next;
        });
      } else {
        if (!userId) return;
        const created = await api.post('/bookmarks/', { user_id: userId, local_program_id: localProgramId });
        setLocalProgramMap((prev) => ({ ...prev, [localProgramId]: created.bookmark_id }));
      }
    } catch {
      // 실패 시 조용히 무시
    }
  }, [localProgramMap, userId]);

  return { isBookmarked, toggleBookmark, isLocalProgramBookmarked, toggleLocalProgramBookmark, loading };
}
