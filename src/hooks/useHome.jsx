import { useState, useEffect } from 'react';
import { api } from '../utils/api';
import usePolicyDetail from './usePolicyDetail';

function mapPolicy(p) {
  return {
    policy_id: p.policy_id,
    plcyNo: p.plcyNo,
    policy_name: p.plcyNm,
    aplyYmd: p.aplyYmd,
    policy_summary: p.policy_summary,
    apply_period_type: p.apply_period_type,
    apply_period: p.apply_period,
    target: p.target,
    maxSprtAmt: p.maxSprtAmt,
    aplyEndDt: p.aplyEndDt,
    banner_reason: p.banner_reason,
  };
}

export default function useHome() {
  const [benefits, setBenefits] = useState([]);
  const [banner, setBanner] = useState([]);
  const [bannerLoading, setBannerLoading] = useState(true);
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
        setBenefits((data || []).map(mapPolicy));
      })
      .catch(() => {
        if (!ignore) setBenefits([]);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    api.get('/policies/home-banner')
      .then((data) => {
        if (ignore) return;
        setBanner((data || []).map(mapPolicy));
      })
      .catch(() => {
        if (!ignore) setBanner([]);
      })
      .finally(() => {
        if (!ignore) setBannerLoading(false);
      });

    return () => { ignore = true; };
  }, []);

  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();

  return {
    benefits, banner, bannerLoading, loading, userName,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  };
}