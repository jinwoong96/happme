import { useState, useEffect } from 'react';
import { api } from '../utils/api';

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
    let ignore = false;

    api.get('/policies/?limit=3')
      .then((data) => {
        if (ignore) return;
        setBenefits((data || []).map((p) => ({ id: p.policy_id, plcyNm: p.plcyNm, aplyYmd: p.aplyYmd })));
        setFeatured(MOCK_FEATURED);
      })
      .catch(() => {
        if (!ignore) setBenefits([]);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => { ignore = true; };
  }, []);

  return { benefits, featured, loading, userName };
}
