import { useState } from 'react';
import { api } from '../utils/api';
import { INQUIRY_TYPES } from '../Pages/Support/inquiryConfig';

export default function useInquiryForm(type) {
  const config = INQUIRY_TYPES[type];
  const [form, setForm] = useState(() =>
    Object.fromEntries((config?.fields ?? []).map((f) => [f.name, '']))
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.post(config.endpoint, config.buildBody(form));
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { config, form, loading, error, submitted, handleChange, handleSubmit };
}
