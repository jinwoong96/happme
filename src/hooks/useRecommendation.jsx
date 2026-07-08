import { useEffect, useRef, useState } from 'react';
import { api } from '../utils/api';

export default function useRecommendation() {
  const [regionChoice, setRegionChoice] = useState('지역 이동 안함');
  const [regionText, setRegionText] = useState('');
  const [employmentChoice, setEmploymentChoice] = useState('없음');
  const [employmentOther, setEmploymentOther] = useState('');
  const [situation, setSituation] = useState('');

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  // "AI 분석 시작" 버튼은 Q3(상황 설명)까지 채워야 활성화된다.
  const canAnalyze = !loading && regionChoice && employmentChoice && situation.trim();

  // 실제 API 호출 로직. situationText를 인자로 받아서, 버튼 클릭(situation 필수)과
  // 페이지 진입 시 자동 호출(situation 없이도 실행) 양쪽에서 재사용한다.
  const runAnalysis = async (situationText) => {
    setLoading(true);
    setError('');
    try {
      const data = await api.post('/recommendations/scenario', {
        region_choice: regionChoice,
        region_text: regionChoice === '지역 쓰기' ? regionText : null,
        employment_choice: employmentChoice,
        employment_other: employmentChoice === '기타' ? employmentOther : null,
        situation: situationText,
      });
      setResults({
        available: data?.available_policies || [],
        closedOrExpired: data?.closed_or_expired_policies || [],
        unavailable: data?.unavailable_policies || [],
      });
    } catch (err) {
      setError(err.message || 'AI 분석에 실패했습니다.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    if (!canAnalyze) return;
    runAnalysis(situation);
  };

  // 페이지 진입 시 한 번, Q1/Q2 기본값("지역 이동 안함"/"없음") + 빈 situation으로
  // 현재 프로필 기준 기본 추천을 자동으로 띄운다. 버튼의 situation 필수 조건(canAnalyze)은 거치지 않는다.
  const hasAutoAnalyzedRef = useRef(false);
  useEffect(() => {
    if (hasAutoAnalyzedRef.current) return;
    hasAutoAnalyzedRef.current = true;
    runAnalysis('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openPolicy = async (policyId, fallbackName, fallbackBookmarked) => {
    if (policyId == null) {
      setSelectedPolicy({
        policy_id: null, plcyNm: fallbackName, is_bookmarked: fallbackBookmarked,
        error: '아직 정책 DB에 등록되지 않아 상세 정보를 볼 수 없어요.',
      });
      return;
    }

    setSelectedPolicy({ policy_id: policyId, plcyNm: fallbackName, is_bookmarked: fallbackBookmarked });
    setPolicyLoading(true);
    try {
      const data = await api.get(`/policies/${policyId}`);
      setSelectedPolicy({ ...data, is_bookmarked: fallbackBookmarked });
    } catch (err) {
      setSelectedPolicy({ policy_id: policyId, plcyNm: fallbackName, is_bookmarked: fallbackBookmarked, error: err.message || '정책 정보를 불러오지 못했습니다.' });
    } finally {
      setPolicyLoading(false);
    }
  };

  const closePolicy = () => setSelectedPolicy(null);

  return {
    regionChoice, setRegionChoice, regionText, setRegionText,
    employmentChoice, setEmploymentChoice, employmentOther, setEmploymentOther,
    situation, setSituation,
    canAnalyze, results, loading, error, handleAnalyze,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  };
}
