import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import usePolicyDetail from './usePolicyDetail';

const MOCK_FEATURED = {
  title: '청년 내일저축계좌',
  description: '최대 1,440만원 지원',
  deadline: '~2024.12.31',
};

export default function useHome() {
  const [benefits, setBenefits] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userName, setUserName] = useState('');

  useEffect(() => {
    let ignore = false;

    api.get('/users/me')
      .then((data) => {
        if (!ignore) setUserName(data.name || '사용자');
      })
      .catch(() => {
        if (!ignore) setUserName(localStorage.getItem('username') || '사용자');
      });

    api.get('/policies/?limit=3&sort=popular')
      .then((data) => {
        if (ignore) return;
        setBenefits((data || []).map((p) => ({
          policy_id: p.policy_id,
          plcyNo: p.plcyNo,
          policy_name: p.plcyNm,
          aplyYmd: p.aplyYmd,
          policy_summary: p.policy_summary,
          apply_period_type: p.apply_period_type,
          apply_period: p.apply_period,
          target: p.target,
        })));
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

  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();

  return { benefits, featured, loading, userName, selectedPolicy, policyLoading, openPolicy, closePolicy };
}