import { useState } from 'react';

export default function useRecommendation() {
  const [scenario, setScenario] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!scenario.trim()) return;
    setLoading(true);
    try {
      // 임시: 백엔드 AI 연결 전 mock 결과
      await new Promise((r) => setTimeout(r, 1500));
      setResults([
        { id: 1, title: '청년 내일저축계좌', reason: '독립 거주 + SW 교육 중인 청년에게 적합', amount: '최대 1,440만원' },
        { id: 2, title: 'K-디지털 트레이닝', reason: 'IT 취업 준비 중인 청년 대상', amount: '최대 200만원' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return { scenario, setScenario, results, loading, handleAnalyze };
}
