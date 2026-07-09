import { useState } from 'react';
import { api } from '../utils/api';

export default function usePolicyDetail() {
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);

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

  return { selectedPolicy, policyLoading, openPolicy, closePolicy };
}
