import { useState, useEffect } from 'react';

const MOCK_BENEFITS = [
  { id: 1, plcyNm: '청년 내일저축계좌', aplyYmd: '2024.12.31' },
  { id: 2, plcyNm: '청년 주거급여 분리지급', aplyYmd: '2024.11.30' },
  { id: 3, plcyNm: 'K-디지털 트레이닝', aplyYmd: '2025.03.31' },
];

const MOCK_FEATURED = {
  title: '청년 내일저축계좌',
  description: '최대 1,440만원 지원',
  deadline: '~2024.12.31',
};

export default function useHome() {
  const [benefits, setBenefits] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [loading, setLoading] = useState(true);
  const userName = localStorage.getItem('userName') || '홍길동';

  useEffect(() => {
    // 임시: 백엔드 연결 전 mock 데이터
    setTimeout(() => {
      setBenefits(MOCK_BENEFITS);
      setFeatured(MOCK_FEATURED);
      setLoading(false);
    }, 500);
  }, []);

  return { benefits, featured, loading, userName };
}
