import { useNavigate } from 'react-router-dom';
import { Bell, RefreshCw, List, Sparkles, FileText, ScanSearch, BellRing, Bookmark, ChevronRight } from 'lucide-react';
import useHome from '../../hooks/useHome';

const MENU = [
  { label: '카테고리', path: '/category', Icon: List },
  { label: '맞춤추천', path: '/recommendation', Icon: Sparkles },
  { label: '공고요약', path: '/summary', Icon: FileText },
  { label: 'OCR분석', path: '/ocr', Icon: ScanSearch },
  { label: '지원금알림', path: '/notification', Icon: BellRing },
  { label: '즐겨찾기', path: '/bookmark', Icon: Bookmark },
];

const TAG_COLOR = {
  인기:   { bg: 'bg-red-50',    text: 'text-red-400' },
  마감임박: { bg: 'bg-orange-50', text: 'text-orange-400' },
  신규:   { bg: 'bg-green-50',  text: 'text-green-400' },
  교육:   { bg: 'bg-blue-50',   text: 'text-blue-400' },
  취업:   { bg: 'bg-purple-50', text: 'text-purple-400' },
};

export default function HomePage() {
  const { benefits, featured, loading, userName } = useHome();
  const navigate = useNavigate();

  return (
    <div className="bg-[#f5f6fa]">
      {/* 헤더 */}
      <div className="flex justify-between items-start px-5 pt-5 pb-4 bg-white">
        <div>
          <p className="m-0 text-[13px] text-[#aaa]">안녕하세요</p>
          <p className="m-0 mt-0.5 text-[22px] font-extrabold text-[#111]">{userName}님 👋</p>
        </div>
        <div className="flex gap-2 mt-1">
          <button className="w-[38px] h-[38px] rounded-full border border-[#eee] bg-white flex items-center justify-center cursor-pointer">
            <Bell size={18} color="#555" />
          </button>
          <button className="w-[38px] h-[38px] rounded-full border border-[#eee] bg-white flex items-center justify-center cursor-pointer">
            <RefreshCw size={16} color="#555" />
          </button>
        </div>
      </div>

      <div className="px-4 pt-4">
        {/* 추천 배너 */}
        {featured && (
          <div className="bg-gradient-to-br from-blue-400 to-blue-500 rounded-[22px] p-[22px] mb-5 shadow-[0_8px_24px_rgba(59,130,246,0.3)]">
            <p className="m-0 text-[12px] text-white/75 font-medium">이번 달 추천 지원금</p>
            <p className="m-0 mt-1.5 mb-1 text-[20px] font-extrabold text-white">{featured.title}</p>
            <p className="m-0 text-[13px] text-white/85">{featured.description} · {featured.deadline}</p>
            <button
              onClick={() => navigate('/category')}
              className="mt-4 flex items-center gap-1 px-4 py-2 rounded-[12px] bg-white/20 text-white text-[13px] font-semibold border-none cursor-pointer"
            >
              자세히 보기 <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* 서비스 메뉴 */}
        <div className="bg-white rounded-[20px] px-4 py-[18px] mb-5 shadow-[0_2px_12px_rgba(0,0,0,0.05)]">
          <p className="m-0 mb-3.5 text-[16px] font-bold text-[#111]">서비스 메뉴</p>
          <div className="grid grid-cols-3 gap-2.5">
            {MENU.map(({ label, path, Icon }) => (
              <button
                key={label}
                onClick={() => navigate(path)}
                className="flex flex-col items-center gap-2 py-4 px-2 rounded-[16px] bg-[#f8f9ff] border-none cursor-pointer"
              >
                <div className="w-11 h-11 rounded-[14px] bg-blue-50 flex items-center justify-center">
                  <Icon size={22} color="#3b82f6" strokeWidth={1.8} />
                </div>
                <span className="text-[12px] text-[#444] font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 인기 지원금 */}
        <div className="mb-5">
          <div className="flex justify-between items-center mb-3">
            <p className="m-0 text-[16px] font-bold text-[#111]">인기 지원금</p>
            <button onClick={() => navigate('/category')} className="text-[13px] text-[#aaa] bg-transparent border-none cursor-pointer">
              전체보기
            </button>
          </div>
          <div className="flex flex-col gap-2.5">
            {loading ? (
              <div className="bg-white rounded-[16px] p-5 text-center text-[13px] text-[#aaa]">불러오는 중...</div>
            ) : (
              benefits.map((item) => {
                const tag = TAG_COLOR[item.tag] || { bg: 'bg-gray-100', text: 'text-gray-400' };
                return (
                  <div key={item.id} className="bg-white rounded-[16px] px-[18px] py-4 shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
                    <span className={`inline-block px-2.5 py-0.5 rounded-lg text-[11px] font-bold ${tag.bg} ${tag.text}`}>
                      {item.tag}
                    </span>
                    <p className="m-0 mt-2 mb-0.5 text-[15px] font-bold text-[#111]">{item.title}</p>
                    <p className="m-0 text-[12px] text-[#aaa]">{item.org}</p>
                    <p className="m-0 mt-1.5 text-[16px] font-extrabold text-blue-500">{item.amount}</p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
