import { useState } from 'react';

export default function useOCR() {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setResults(null);
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setLoading(true);
    try {
      // 임시: 백엔드 OCR 연결 전 mock
      await new Promise((r) => setTimeout(r, 2000));
      setResults({
        extracted: '국민취업지원제도 - 구직촉진수당 최대 300만원, 취업 활동 비용 지원',
        matched: ['국민취업지원제도', '청년 취업 지원금'],
      });
    } finally {
      setLoading(false);
    }
  };

  return { files, loading, results, handleFileChange, handleAnalyze };
}
