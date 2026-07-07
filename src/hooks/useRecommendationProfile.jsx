import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const EMPTY_FORM = {
  birth_date: '',
  gender: '',
  region: '',
  district: '',

  education: '',
  school_name: '',
  major: '',
  student_status: '',
  graduation_year: '',

  employment_status: '',
  occupation: '',
  job_seeking: false,
  career_history: '',

  monthly_income: '',
  household_income_ratio: '',
  household_size: '',
  assets: '',

  marital_status: '',
  disability: false,
  veteran: false,
  military_status: '',

  startup_interest: false,
  business_owner: false,
  startup_status: '',
  company_type: '',

  housing_status: '',
  situation: '',
  reason: '',
};

const NUMBER_FIELDS = ['graduation_year', 'monthly_income', 'household_income_ratio', 'household_size', 'assets'];
const BOOLEAN_FIELDS = ['job_seeking', 'disability', 'veteran', 'startup_interest', 'business_owner'];

export default function useRecommendationProfile() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;

    api.get('/profiles/me').catch(() => null).then((profile) => {
      if (ignore) return;
      if (profile) {
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

      navigate('/recommendation');
    } catch (err) {
      setError(err.message || '프로필 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  return { form, handleChange, handleSubmit, loading, saving, error };
}
