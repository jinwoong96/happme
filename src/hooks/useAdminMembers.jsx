import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export default function useAdminMembers() {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchMembers = useCallback(() => {
    setLoading(true);
    api.get('/users/')
      .then(setMembers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchMembers(); }, [fetchMembers]);

  const deleteMember = async (userId) => {
    await api.delete(`/users/${userId}`);
    setMembers((prev) => prev.filter((m) => m.user_id !== userId));
  };

  return { members, loading, error, deleteMember };
}
