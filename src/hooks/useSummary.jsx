import { useState } from 'react';
import { api } from '../utils/api';

const KNOWN_LABELS = [
  '한줄요약', '요약', '지원대상', '지원내용', '신청방법',
  '신청기간', '사업기간', '담당기관', '신청URL', '지원규모', '기타사항', '정책명',
];

function parseSummaryFields(text) {
  if (!text) return {};

  const pattern = new RegExp(`\\*{0,2}(${KNOWN_LABELS.join('|')})\\*{0,2}\\s*[:：]\\s*`, 'g');
  const parts = text.split(pattern); // [머리말, 라벨1, 값1, 라벨2, 값2, ...]

  const fields = {};
  for (let i = 1; i < parts.length; i += 2) {
    const label = parts[i];
    const value = (parts[i + 1] || '').trim();
    if (value) fields[label] = value;
  }
  return fields;
}

export default function useSummary() {
  const [files, setFiles] = useState([]);
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [results, setResults] = useState(null);
  const [policyName, setPolicyName] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [asking, setAsking] = useState(false);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setResults(null);
    setError(null);
  };

  const handleTextChange = (e) => {
    setText(e.target.value);
    setResults(null);
    setError(null);
  };

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
    setResults(null);
    setError(null);
  };

  const canSummarize = !loading && (files.length > 0 || text.trim().length > 0 || url.trim().length > 0);

  const applyAiResult = (aiResult) => {
    const first = aiResult?.results?.[0];

    if (!first?.matched) {
      setResults(null);
      setPolicyName(null);
      setError(
        first?.method === '크롤링차단'
          ? '이 사이트는 분석할 수 없어요. PDF를 다운로드하거나 텍스트를 복사해서 입력해주세요.'
          : '해당하는 정책을 찾지 못했어요.'
      );
      return;
    }

    const fields = parseSummaryFields(first.summary);
    const entries = Object.entries(fields);

    setPolicyName(first.policy_name);
    setResults({
      title: first.policy_name,
      // 라벨(**지원대상** 등)이 파싱되면 번호 목록으로, 안 되면 원문 그대로
      summaryLines: entries.length > 0
        ? entries.map(([label, value], i) => `${i + 1}. ${label}: ${value}`)
        : [(first.summary || '').replace(/\*\*/g, '')],
    });
    setAnswer(null);
  };


  const handleSummarize = async () => {
    console.log('클릭됨', { canSummarize, files, text, url });
    if (!canSummarize) return;
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      let res;
      if (files.length > 0) {
        const formData = new FormData();
        files.forEach((f) => formData.append('files', f));
        res = await api.postForm('/pdf/analyze', formData);
      } else if (text.trim().length > 0) {
        res = await api.post('/pdf/analyze-text', { text });
      } else {
        res = await api.post('/pdf/analyze-url', { url });
      }
      console.log('서버 응답', res);
      applyAiResult(res.ai_result);
      applyAiResult(res.ai_result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim() || !policyName) return;
    setAsking(true);
    try {
      const res = await api.post('/pdf/ask', { policy_name: policyName, question });
      setAnswer(res.answer);
    } catch (e) {
      setAnswer(e.message);
    } finally {
      setAsking(false);
    }
  };

  return {
    files, text, url, results, loading, error,
    question, answer, asking,
    handleFileChange, handleTextChange, handleUrlChange,
    handleSummarize, canSummarize,
    setQuestion, handleAsk,
  };
}
