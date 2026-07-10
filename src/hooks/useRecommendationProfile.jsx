import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../utils/api';

const EMPTY_FORM = {
  birth_date: '',
  gender: '',
  region: '',
  district: '',

  education: '',
  school_name: '',
  major: '',
  major_category: '기타',
  student_status: '',
  graduation_year: '',

  employment_status: '기타',
  occupation: '',
  job_seeking: false,
  career_history: '',

  marital_status: '',
  disability: false,
  basic_livelihood: false,
  single_parent: false,

  startup_interest: false,
  business_owner: false,
  startup_status: '',
  company_type: '해당 없음',

  housing_status: '',
  situation: '',
  reason: '',
};

const NUMBER_FIELDS = ['graduation_year'];
const BOOLEAN_FIELDS = [
  'job_seeking', 'disability', 'basic_livelihood', 'single_parent',
  'startup_interest', 'business_owner',
];
const REQUIRED_FIELDS = ['birth_date', 'gender', 'region', 'education', 'employment_status', 'marital_status'];

export default function useRecommendationProfile() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from === 'mypage' ? 'mypage' : 'recommendation';
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

      navigate(from === 'mypage' ? '/mypage' : '/recommendation');
    } catch (err) {
      setError(err.message || '프로필 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    navigate('/recommendation');
  };

  return { form, handleChange, handleSubmit, handleSkip, loading, saving, error, from, hasProfile, requiredFields: REQUIRED_FIELDS };
}
