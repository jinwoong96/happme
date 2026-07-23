import { useState } from 'react';
import { api } from '../utils/api';

// 정책 상세 모달 상태를 관리하는 공용 훅. 여러 화면(홈/카테고리/추천 등)에서 재사용된다.
export default function usePolicyDetail() {
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  // 정책 상세 모달을 연다. policyId가 없으면(아직 DB 미등록 정책) 상세 조회 없이
  // 안내 메시지만 보여준다. 우선 카드에 있던 값(fallback)으로 즉시 표시한 뒤 상세를 채운다.
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
