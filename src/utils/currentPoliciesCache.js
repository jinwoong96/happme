// "가능정책" 탭(현재 프로필 기준 추천)은 저장해두고 계속 볼 수 있어야 하므로,
// 매번 다시 계산하지 않고 localStorage에 캐시해둔다.
// 프로필이 바뀌면(useRecommendationProfile에서 저장 성공 시) 캐시를 지워서 다음 진입 시 새로 계산되게 한다.
const CACHE_KEY = 'bene:currentPolicies';

export function readCurrentPoliciesCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function writeCurrentPoliciesCache(results) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(results));
  } catch {
    // 저장 실패는 무시한다 (다음 진입 시 다시 계산됨)
  }
}

export function clearCurrentPoliciesCache() {
  try {
    localStorage.removeItem(CACHE_KEY);
  } catch {
    // ignore
  }
}