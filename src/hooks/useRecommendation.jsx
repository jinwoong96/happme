import { useState } from 'react';
import { api } from '../utils/api';

export default function useRecommendation() {
  const [scenario, setScenario] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!scenario.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.post('/recommendations/chat', { chat: scenario });
      setResults({
        available: data?.available_policies || [],
        closed: data?.closed_policies || [],
        expired: data?.expired_policies || [],
        unavailable: data?.unavailable_policies || [],
      });
    } catch (err) {
      setError(err.message || 'AI 분석에 실패했습니다.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

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
    scenario, setScenario, results, loading, error, handleAnalyze,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  };
}
