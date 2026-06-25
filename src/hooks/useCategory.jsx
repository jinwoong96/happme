import { useState, useEffect } from 'react';

const CATEGORIES = ['지원금', '인턴', '정부', '사업', '지역'];

const MOCK_DATA = {
  지원금: [
    { id: 1, tag: '인기', title: '청년 내일저축계좌', org: '보건복지부', amount: '최대 1,440만원', deadline: '2024.12.31' },
    { id: 2, tag: '마감임박', title: '청년 주거급여 분리지급', org: '국토교통부', amount: '월 최대 341,000원', deadline: '2024.11.30' },
    { id: 3, tag: '신규', title: 'K-디지털 트레이닝', org: '고용노동부', amount: '최대 200만원', deadline: '2025.03.31' },
    { id: 4, tag: '교육', title: '삼성 청년 SW 아카데미', org: '삼성전자', amount: '월 100만원', deadline: '2025.01.15' },
    { id: 5, tag: '취업', title: '현대차 청년 취업 지원금', org: '현대자동차', amount: '최대 50만원', deadline: '2025.02.28' },
  ],
  인턴: [],
  정부: [],
  사업: [],
  지역: [],
};

export default function useCategory() {
  const [activeTab, setActiveTab] = useState('지원금');
  const [items, setItems] = useState([]);
  const [bookmarks, setBookmarks] = useState(new Set());

  useEffect(() => {
    setItems(MOCK_DATA[activeTab] || []);
  }, [activeTab]);

  const toggleBookmark = (id) => {
    setBookmarks((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return { categories: CATEGORIES, activeTab, setActiveTab, items, bookmarks, toggleBookmark };
}
