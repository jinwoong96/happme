import { useNavigate } from 'react-router-dom';

// 고객지원 메인 화면: 문의 유형 카드를 누르면 해당 문의 폼 페이지로 이동시킨다.
export default function useSupport() {
  const navigate = useNavigate();

  const handleContact = (type) => {
    navigate(`/support/${type}`);
  };

  return { handleContact };
}
