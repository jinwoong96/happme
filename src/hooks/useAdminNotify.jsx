import { useState } from 'react';
import { api } from '../utils/api';

export default function useAdminNotify() {
  const [form, setForm] = useState({ title: '', content: '', is_pinned: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.title.trim() || !form.content.trim()) {
      setError('제목과 내용을 입력해주세요.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/notifications/broadcast', form);
      setDone(true);
      setForm({ title: '', content: '', is_pinned: false });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { form, loading, error, done, setDone, handleChange, handleSubmit };
}
