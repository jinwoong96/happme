import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../utils/api';
import { clearCurrentPoliciesCache } from '../utils/currentPoliciesCache';

const EMPTY_FORM = {
  birth_date: '',
  gender: '',
  region: '',
  district: '',

  education: '',
  major_category: '기타',

  employment_status: '기타',
  sme_employment: false,

  marital_status: '',
  disability: false,
  basic_livelihood: false,
  single_parent: false,

  situation: '',
};

const NUMBER_FIELDS = [];
const BOOLEAN_FIELDS = ['sme_employment', 'disability', 'basic_livelihood', 'single_parent'];
const REQUIRED_FIELDS = ['birth_date', 'gender', 'region', 'education', 'employment_status', 'marital_status'];

// 추천에 쓰이는 사용자 프로필 입력/수정 폼을 관리한다. 저장 후 어디로 돌아갈지는
// 진입 경로(from: mypage/current/recommendation)에 따라 달라진다.
export default function useRecommendationProfile() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from === 'mypage'
    ? 'mypage'
    : location.state?.from === 'current'
      ? 'current'
      : 'recommendation';
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    let ignore = false;

    api.get('/profiles/me').catch(() => null).then((profile) => {
      if (ignore) return;
      if (profile) {
        setHasProfile(true);
        setForm((prev) => {
          const next = { ...prev };
          for (const key of Object.keys(EMPTY_FORM)) {
            if (profile[key] === undefined || profile[key] === null) continue;
            next[key] = profile[key];
          }
          return next;
        });
      }
    }).finally(() => {
      if (!ignore) setLoading(false);
    });

    return () => { ignore = true; };
  }, []);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setError('');

    const hasMissingRequired = REQUIRED_FIELDS.some((key) => !form[key]);
    if (hasMissingRequired) {
      setError('필수 항목을 모두 입력해주세요.');
      return;
    }

    setSaving(true);
    try {
      const payload = {};
      for (const key of Object.keys(EMPTY_FORM)) {
        const value = form[key];
        if (BOOLEAN_FIELDS.includes(key)) {
          payload[key] = Boolean(value);
        } else if (NUMBER_FIELDS.includes(key)) {
          payload[key] = value === '' ? null : Number(value);
        } else {
          payload[key] = value === '' ? null : value;
        }
      }

      // 프로필이 있으면 수정, 없으면 생성 (백엔드에서 통합 처리)
      await api.put('/profiles/me', payload);

  // 프로필이 바뀌었으니 "가능정책" 캐시는 다음 진입 시 새로 계산되게 지운다.
      clearCurrentPoliciesCache();

      const destination = from === 'mypage' ? '/mypage' : from === 'current' ? '/recommendation/current' : '/recommendation';
      navigate(destination);
    } catch (err) {
      setError(err.message || '프로필 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    navigate(from === 'current' ? '/recommendation/current' : '/recommendation');
  };

  return { form, handleChange, handleSubmit, handleSkip, loading, saving, error, from, hasProfile, requiredFields: REQUIRED_FIELDS };
}