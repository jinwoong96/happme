import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';
import usePolicyDetail from './usePolicyDetail';

// "무엇이 바뀌면" 시뮬레이션 추천 화면: Q1(지역이동)/Q2(취업변화)/Q3(상황설명) 답변으로
// what-if 추천을 요청하고, 결과와 정책 상세 모달을 관리한다.
export default function useRecommendation() {
  const navigate = useNavigate();
  const [regionChoice, setRegionChoice] = useState('지역 이동 안함');
  const [regionText, setRegionText] = useState('');
  const [employmentChoice, setEmploymentChoice] = useState('없음');
  const [employmentOther, setEmploymentOther] = useState('');
  const [situation, setSituation] = useState('');

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();

  // "AI 분석 시작" 버튼은 Q3(상황 설명)까지 채워야 활성화된다.
  const canAnalyze = !loading && regionChoice && employmentChoice && situation.trim();

  // 실제 API 호출 로직. situation은 handleAnalyze(버튼 클릭)에서만 채워져서 넘어온다.
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
        wide: data?.wide_policies || [],
        province: data?.province_policies || [],
        local: data?.local_policies || [],
        llmAnswer: data?.llm_answer || null,
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

  // 이 페이지는 시뮬레이션(미래 상황) 전용이라 진입 시 자동으로 분석을 돌리지 않는다.
  // (현재 프로필만으로 보는 추천은 "가능정책" 페이지로 분리됨.)
  // 다만 시뮬레이션도 저장된 프로필 위에 diff를 얹는 방식이라, 프로필이 없으면 먼저 입력받는다.
  useEffect(() => {
    let ignore = false;

    api.get('/profiles/me').catch(() => null).then((profile) => {
      if (ignore) return;
      if (!profile) {
        navigate('/recommendation/profile', { state: { from: 'recommendation' }, replace: true });
      }
    });

    return () => { ignore = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    regionChoice, setRegionChoice, regionText, setRegionText,
    employmentChoice, setEmploymentChoice, employmentOther, setEmploymentOther,
    situation, setSituation,
    canAnalyze, results, loading, error, handleAnalyze,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  };
}