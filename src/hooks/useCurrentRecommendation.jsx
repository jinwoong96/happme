import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import usePolicyDetail from './usePolicyDetail';

// "가능정책" 탭: 시나리오 입력 없이 저장된 프로필만으로 받는 순수 추천.
// POST /recommendations/(순수 프로필 추천)는 백엔드에서 bene_ai의 다른 응답 형태(available_policies 등)를
// 그대로 돌려주다 프론트가 기대하는 형태와 안 맞아 500 에러가 나서, 이미 검증된
// /recommendations/chat(빈 문자열)을 대신 쓴다. chat이 빈 문자열이면 유사도 재정렬 없이
// rule engine 판정 순서 그대로 wide/province/local 버킷으로 내려온다(백엔드 주석 참고).
// 정책 데이터/판정 로직이 계속 바뀔 수 있어(최신화, eligibility 로직 변경 등) 결과를 로컬에
// 캐시하지 않고 화면 진입마다 항상 새로 계산한다.
export default function useCurrentRecommendation() {
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();

  const fetchRecommendation = async ({ silent } = {}) => {
    if (silent) setRefreshing(true); else setLoading(true);
    setError('');
    try {
      const data = await api.post('/recommendations/chat', { chat: '' });
      const next = {
        wide: data?.wide_policies || [],
        province: data?.province_policies || [],
        local: data?.local_policies || [],
      };
      setResults(next);
    } catch (err) {
      setError(err.message || '추천 정책을 불러오지 못했습니다.');
    } finally {
      if (silent) setRefreshing(false); else setLoading(false);
    }
  };

  // 프로필이 없으면 먼저 입력받고, 있으면 매번 새로 계산한다.
  useEffect(() => {
    let ignore = false;

    api.get('/profiles/me').catch(() => null).then((profile) => {
      if (ignore) return;
      if (!profile) {
        navigate('/recommendation/profile', { state: { from: 'current' }, replace: true });
        return;
      }
      fetchRecommendation();
    });

    return () => { ignore = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refresh = () => fetchRecommendation({ silent: true });

  return {
    results, loading, refreshing, error, refresh,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  };
}