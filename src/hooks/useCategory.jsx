import { useState, useEffect } from 'react';

const CATEGORIES = ['전체', '일자리', '주거', '교육', '복지문화', '참여권리', '지역'];

const MOCK_DATA = [
  { id: 1, category: '복지문화', plcyNm: '청년 내일저축계좌', aplyYmd: '2024.12.31' },
  { id: 2, category: '주거', plcyNm: '청년 주거급여 분리지급', aplyYmd: '2024.11.30' },
  { id: 3, category: '교육', plcyNm: 'K-디지털 트레이닝', aplyYmd: '2025.03.31' },
  { id: 4, category: '교육', plcyNm: '삼성 청년 SW 아카데미', aplyYmd: '2025.01.15' },
  { id: 5, category: '일자리', plcyNm: '현대차 청년 취업 지원금', aplyYmd: '2025.02.28' },
  { id: 6, category: '참여권리', plcyNm: '청년참여 정책 서포터즈', aplyYmd: '' },
  { id: 7, category: '지역', plcyNm: '지역 청년 정착 지원금', aplyYmd: '2025.06.30' },
];

export default function useCategory() {
  const [activeTab, setActiveTab] = useState('전체');
  const [items, setItems] = useState([]);
  const [bookmarks, setBookmarks] = useState(new Set());

  useEffect(() => {
    setItems(activeTab === '전체' ? MOCK_DATA : MOCK_DATA.filter((item) => item.category === activeTab));
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
