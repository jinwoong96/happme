import { Bookmark } from 'lucide-react';
import useCategory from '../../hooks/useCategory';

const TAG_COLOR = {
  인기:   { bg: 'bg-red-50',    text: 'text-red-400' },
  마감임박: { bg: 'bg-orange-50', text: 'text-orange-400' },
  신규:   { bg: 'bg-green-50',  text: 'text-green-400' },
  교육:   { bg: 'bg-blue-50',   text: 'text-blue-400' },
  취업:   { bg: 'bg-purple-50', text: 'text-purple-400' },
};

export default function CategoryPage() {
  const { categories, activeTab, setActiveTab, items, bookmarks, toggleBookmark } = useCategory();

  return (
    <div className="bg-[#f5f6fa]">
      <div className="px-5 pt-5 pb-4 bg-white">
        <p className="m-0 text-[22px] font-extrabold text-[#111]">카테고리</p>
      </div>

      {/* 탭 */}
      <div className="flex gap-2 px-4 py-3 bg-white border-b border-gray-100 overflow-x-auto">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveTab(cat)}
            className={`px-[18px] py-2 rounded-[20px] text-[13px] font-semibold whitespace-nowrap border-none cursor-pointer transition-all ${
              activeTab === cat ? 'bg-blue-500 text-white' : 'bg-gray-100 text-[#666]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* 목록 */}
      <div className="px-4 pt-3.5 flex flex-col gap-2.5">
        {items.length === 0 ? (
          <div className="text-center py-10 text-[13px] text-[#aaa]">항목이 없습니다.</div>
        ) : (
          items.map((item) => {
            const tag = TAG_COLOR[item.tag] || { bg: 'bg-gray-100', text: 'text-gray-400' };
            return (
              <div key={item.id} className="bg-white rounded-[18px] px-[18px] py-4 flex justify-between items-start shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
                <div className="flex-1">
                  <span className={`inline-block px-2.5 py-0.5 rounded-lg text-[11px] font-bold ${tag.bg} ${tag.text}`}>
                    {item.tag}
                  </span>
                  <p className="m-0 mt-2 mb-0.5 text-[15px] font-bold text-[#111]">{item.title}</p>
                  <p className="m-0 text-[12px] text-[#aaa]">{item.org}</p>
                  <p className="m-0 mt-1.5 text-[16px] font-extrabold text-blue-500">{item.amount}</p>
                </div>
                <div className="flex flex-col items-end gap-1.5 ml-2.5">
                  <button onClick={() => toggleBookmark(item.id)} className="bg-transparent border-none cursor-pointer p-0.5">
                    <Bookmark size={18} color={bookmarks.has(item.id) ? '#3b82f6' : '#ccc'} fill={bookmarks.has(item.id) ? '#3b82f6' : 'none'} />
                  </button>
                  <span className="text-[11px] text-[#ccc]">~{item.deadline}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
