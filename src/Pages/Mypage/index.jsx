import { Bookmark, Bell, UserPen, Lock, Headphones, FileText, ChevronRight } from 'lucide-react';
import useMypage from '../../hooks/useMypage';

const MENU_ITEMS = [
  { Icon: Bookmark,   label: '즐겨찾기 목록' },
  { Icon: Bell,       label: '알림 설정' },
  { Icon: UserPen,    label: '프로필 수정' },
  { Icon: Lock,       label: '비밀번호 변경' },
  { Icon: Headphones, label: '고객센터' },
  { Icon: FileText,   label: '이용약관' },
];

export default function MypagePage() {
  const { user, handleLogout } = useMypage();
  if (!user) return null;

  const STATS = [
    { label: '즐겨찾기', value: user.bookmarkCount },
    { label: '신청 완료', value: 0 },
    { label: '알림', value: 2 },
  ];

  return (
    <div className="bg-[#f5f6fa]">
      <div className="px-5 pt-5 pb-4 bg-white">
        <p className="m-0 text-[22px] font-extrabold text-[#111]">마이</p>
      </div>

      {/* 프로필 카드 */}
      <div className="mx-4 mt-4 bg-white rounded-[20px] p-5 shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
        <div className="flex items-center gap-3.5">
          <div className="w-[58px] h-[58px] rounded-full bg-gradient-to-br from-blue-400 to-blue-500 flex items-center justify-center text-white text-[22px] font-bold shrink-0">
            {user.name[0]}
          </div>
          <div>
            <p className="m-0 text-[18px] font-bold text-[#111]">{user.name}</p>
            <p className="m-0 mt-0.5 text-[13px] text-[#aaa]">{user.email}</p>
          </div>
        </div>
        <div className="flex gap-2.5 mt-[18px]">
          {STATS.map(({ label, value }) => (
            <div key={label} className="flex-1 bg-[#f8f9ff] rounded-[14px] py-3 px-2 text-center">
              <p className="m-0 text-[20px] font-extrabold text-blue-500">{value}</p>
              <p className="m-0 mt-0.5 text-[11px] text-[#aaa]">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 메뉴 */}
      <div className="mx-4 mt-4 bg-white rounded-[20px] overflow-hidden shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
        {MENU_ITEMS.map(({ Icon, label }, i) => (
          <button
            key={label}
            className={`w-full flex items-center gap-3.5 px-[18px] py-4 bg-transparent border-none cursor-pointer text-left ${i < MENU_ITEMS.length - 1 ? 'border-b border-gray-50' : ''}`}
          >
            <Icon size={18} color="#555" strokeWidth={1.8} />
            <span className="flex-1 text-[14px] text-[#333] font-medium">{label}</span>
            <ChevronRight size={16} color="#ccc" />
          </button>
        ))}
      </div>

      {/* 로그아웃 */}
      <div className="mx-4 mt-4 mb-6">
        <button
          onClick={handleLogout}
          className="w-full py-[15px] rounded-[16px] bg-white text-red-400 text-[15px] font-bold border border-red-100 cursor-pointer"
        >
          로그아웃
        </button>
      </div>
    </div>
  );
}
