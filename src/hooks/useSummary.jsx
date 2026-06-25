import { useState } from 'react';

export default function useSummary() {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files));
    setResults(null);
  };

  const handleSummarize = async () => {
    if (files.length === 0) return;
    setLoading(true);
    try {
      // 임시: 백엔드 연결 전 mock
      await new Promise((r) => setTimeout(r, 2000));
      setResults({
        title: '2024년 청년 내일저축계좌 모집 공고',
        summary: '만 19~34세 청년 중 근로·사업소득이 있는 경우 신청 가능합니다. 본인이 매월 10만원을 저축하면 정부가 최대 30만원을 추가 지원하며, 3년 만기 시 최대 1,440만원을 수령할 수 있습니다.',
        keyPoints: [
          '신청 자격: 만 19~34세, 근로·사업소득 보유자',
          '지원 금액: 정부 매칭 최대 월 30만원',
          '신청 기간: 2024.10.01 ~ 2024.12.31',
          '제출 서류: 소득 증빙 서류, 신분증 사본',
          '문의처: 보건복지부 콜센터 129',
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  return { files, loading, results, handleFileChange, handleSummarize };
}
