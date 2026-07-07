import { useNavigate } from 'react-router-dom';

export default function useSupport() {
  const navigate = useNavigate();

  const handleContact = (type) => {
    navigate(`/support/${type}`);
  };

  return { handleContact };
}
