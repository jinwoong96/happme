import { useState, useEffect, useRef } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082';
const SESSION_KEY = 'bene_ocr_state';

function loadPersisted() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function savePersisted(state) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(state));
  } catch {
    // 저장 실패는 무시 (용량 초과 등)
  }
}

function clearPersisted() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    // 무시
  }
}

export default function useOCR() {
  const persisted = loadPersisted();

  const [files, setFiles] = useState([]);
  const [previewDataUrl, setPreviewDataUrl] = useState(persisted?.previewDataUrl ?? null);
  const [results, setResults] = useState(persisted?.results ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (results) {
      savePersisted({ results, previewDataUrl });
    }
  }, [results, previewDataUrl]);

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files);
    setFiles(selected);
    setResults(null);
    setError('');

    if (selected[0]) {
      const reader = new FileReader();
      reader.onload = () => setPreviewDataUrl(reader.result);
      reader.readAsDataURL(selected[0]);
    } else {
      setPreviewDataUrl(null);
    }
  };

  const handleRemoveFile = () => {
    setFiles([]);
    setResults(null);
    setError('');
    setPreviewDataUrl(null);
    clearPersisted();
    // input의 value(선택된 파일 경로)를 초기화하지 않으면, 브라우저가 "선택값이
    // 안 바뀌었다"고 판단해서 같은 파일을 다시 골라도 onChange가 아예 안 일어난다.
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError('');
    setResults(null);
    clearPersisted();

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

  const clearOcrSession = clearPersisted;

  return { files, loading, results, error, previewDataUrl, fileInputRef, handleFileChange, handleRemoveFile, handleAnalyze, clearOcrSession };
}