import { useState } from 'react';

const INITIAL = [
  { id: 1, title: '청년 내일저축계좌', org: '보건복지부', deadline: '2024-12-31', on: true },
  { id: 2, title: '청년 주거급여 분리지급', org: '국토교통부', deadline: '2024-11-30', on: false },
  { id: 3, title: 'K-디지털 트레이닝', org: '고용노동부', deadline: '2025-03-31', on: false },
  { id: 4, title: '삼성 청년 SW 아카데미', org: '삼성전자', deadline: '2025-01-15', on: false },
  { id: 5, title: '현대차 청년 취업 지원금', org: '현대자동차', deadline: '2025-02-28', on: false },
  { id: 6, title: '서울시청년수당', org: '서울특별시', deadline: '2024-12-15', on: false },
  { id: 7, title: '청년 창업 인턴십', org: '중소벤처기업부', deadline: '2025-04-30', on: false },
  { id: 8, title: '부산시청년 해양일자리', org: '부산광역시', deadline: '2025-02-14', on: false },
];

export default function useNotification() {
  const [items, setItems] = useState(INITIAL);
  const [search, setSearch] = useState('');

  const toggle = (id) => {
    setItems((prev) => prev.map((item) => item.id === id ? { ...item, on: !item.on } : item));
  };

  const filtered = items.filter((item) =>
    item.title.includes(search) || item.org.includes(search)
  );

  return { filtered, search, setSearch, toggle };
}
