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

// 홈 화면에 머무르는 동안에도 관리자가 새로 등록/수정한 공고문의 키워드 알림이 뜨는지
// 주기적으로 다시 확인한다(관리자 저장 -> AI 임베딩/매칭은 백그라운드라 수 초~수십 초 걸림).
const UNREAD_POLL_MS = 30_000;

export default function useHome() {
  const [benefits, setBenefits] = useState([]);
  const [banner, setBanner] = useState([]);
  const [bannerLoading, setBannerLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [userName, setUserName] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let ignore = false;

    const fetchUnreadCount = () => {
      api.get('/notifications/me?unread_only=true')
        .then((data) => {
          if (!ignore) setUnreadCount((data || []).length);
        })
        .catch(() => {
          if (!ignore) setUnreadCount(0);
        });
    };

    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, UNREAD_POLL_MS);

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

    return () => { ignore = true; clearInterval(interval); };
  }, []);

  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();

  return {
    benefits, banner, bannerLoading, loading, userName, unreadCount,
    selectedPolicy, policyLoading, openPolicy, closePolicy,
  };
}