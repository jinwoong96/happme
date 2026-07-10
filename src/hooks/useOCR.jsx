import { useState } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082';

export default function useOCR() {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setResults(null);
    setError('');
  };

  const handleRemoveFile = () => {
    setFiles([]);
    setResults(null);
    setError('');
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', files[0]);

      const res = await fetch(`${BASE_URL}/ocr/analyze-image`, {
        method: 'POST',
        credentials: 'include', // 로그인 쿠키 포함
        body: formData,
        // Content-Type은 지정하지 않음 (브라우저가 boundary 포함해서 자동 설정)
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || '이미지 분석에 실패했어요. 잠시 후 다시 시도해주세요.');
      }

      const data = await res.json();

      setResults({
        matches: data.matches || [], // [{policy_id, plcyNm, score, sprtTrgtMinAge, sprtTrgtMaxAge, plcySprtCn, aplyYmd, aplyUrlAddr}, ...]
        summary: data.summary_text || null,
        message: data.message || null,
      });
    } catch (err) {
      setError(err.message || '이미지 분석 중 오류가 발생했어요.');
    } finally {
      setLoading(false);
    }
  };

  return { files, loading, results, error, handleFileChange, handleRemoveFile, handleAnalyze };
}