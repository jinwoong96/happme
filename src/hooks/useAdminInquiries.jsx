import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export default function useAdminInquiries() {
  const [inquiries, setInquiries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchInquiries = useCallback(() => {
    setLoading(true);
    api.get('/inquiries/')
      .then(setInquiries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchInquiries(); }, [fetchInquiries]);

  const answerInquiry = async (inquiryId, answer) => {
    const updated = await api.patch(`/inquiries/${inquiryId}/answer`, { answer });
    setInquiries((prev) => prev.map((i) => (i.inquiry_id === inquiryId ? updated : i)));
  };

  return { inquiries, loading, error, answerInquiry };
}
