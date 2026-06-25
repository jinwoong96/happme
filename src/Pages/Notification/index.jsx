import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Search } from 'lucide-react';
import useNotification from '../../hooks/useNotification';

export default function NotificationPage() {
  const { filtered, search, setSearch, toggle } = useNotification();
  const navigate = useNavigate();

  return (
    <div className="bg-[#f5f6fa] h-full flex flex-col">
      <div className="flex items-center gap-2 px-4 pt-5 pb-4 bg-white">
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="m-0 text-[18px] font-bold text-[#111]">지원금 알림</p>
      </div>

      {/* 검색창 */}
      <div className="px-4 py-3 bg-white border-b border-gray-100">
        <div className="flex items-center gap-2.5 bg-[#f5f6fa] rounded-[14px] px-3.5 py-[11px]">
          <Search size={16} color="#aaa" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="지원금 검색..."
            className="flex-1 border-none bg-transparent text-[14px] text-[#333] outline-none"
          />
        </div>
      </div>

      {/* 목록 */}
      <div className="flex-1 overflow-y-auto bg-white">
        {filtered.length === 0 ? (
          <div className="text-center py-10 text-[13px] text-[#aaa]">검색 결과가 없습니다.</div>
        ) : (
          filtered.map((item, i) => (
            <div
              key={item.id}
              className={`flex items-center justify-between px-5 py-4 ${i < filtered.length - 1 ? 'border-b border-gray-50' : ''}`}
            >
              <div className="flex-1 mr-3">
                <p className="m-0 text-[14px] font-semibold text-[#111]">{item.title}</p>
                <p className="m-0 mt-0.5 text-[12px] text-[#aaa]">{item.org} · 마감 {item.deadline}</p>
              </div>

              {/* 토글 */}
              <button
                onClick={() => toggle(item.id)}
                className={`w-[46px] h-[26px] rounded-[13px] border-none cursor-pointer relative shrink-0 transition-colors duration-200 ${item.on ? 'bg-blue-500' : 'bg-gray-200'}`}
              >
                <div className={`absolute top-[3px] w-5 h-5 rounded-full bg-white shadow-[0_1px_4px_rgba(0,0,0,0.2)] transition-all duration-200 ${item.on ? 'left-[23px]' : 'left-[3px]'}`} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
