import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export default function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(() => {
    setLoading(true);
    api.get('/notifications/me')
      .then(setAlerts)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  const markRead = async (id) => {
    await api.patch(`/notifications/${id}/read`);
    setAlerts((prev) => prev.map((a) => (a.notification_id === id ? { ...a, is_read: true } : a)));
  };

  const markAllRead = async () => {
    await api.patch('/notifications/me/read-all');
    setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
  };

  const removeAlert = async (id) => {
    const prev = alerts;
    setAlerts((cur) => cur.filter((a) => a.notification_id !== id));
    try {
      await api.delete(`/notifications/${id}`);
    } catch {
      setAlerts(prev);
    }
  };

  return { alerts, loading, markRead, markAllRead, removeAlert };
}
