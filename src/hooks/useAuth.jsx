import { useState, useEffect } from 'react';
import { api } from '../utils/api';

export default function useAuth() {
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    api.get('/users/me')
      .then((data) => {
        localStorage.setItem('isAuthed', 'true');
        if (data?.name) localStorage.setItem('userName', data.name);
        if (data?.email) localStorage.setItem('userEmail', data.email);
        setStatus('authed');
      })
      .catch(() => {
        localStorage.removeItem('isAuthed');
        localStorage.removeItem('userName');
        localStorage.removeItem('userEmail');
        setStatus('unauthed');
      });
  }, []);

  return { status };
}