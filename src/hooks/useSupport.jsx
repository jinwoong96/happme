import { useState } from 'react';

export default function useSupport() {
  const [submitted, setSubmitted] = useState(false);

  const handleContact = (type) => {
    // 임시: 백엔드 연결 전 mock
    alert(`${type} 문의 페이지로 이동합니다.`);
  };

  return { handleContact, submitted };
}
