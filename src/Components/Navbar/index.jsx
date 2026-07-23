import { NavLink } from 'react-router-dom';
import { Home, Grid2x2, Bookmark, User } from 'lucide-react';

const tabs = [
  { to: '/', label: '홈', Icon: Home },
  { to: '/category', label: '전체보기', Icon: Grid2x2 },
  { to: '/bookmark', label: '즐겨찾기', Icon: Bookmark },
  { to: '/mypage', label: '마이페이지', Icon: User },
];

// 하단 탭 네비게이션(홈/전체보기/즐겨찾기/마이페이지).
export default function Navbar() {
  return (
    <nav className="flex justify-around items-center bg-white border-t border-gray-100 py-2.5 shrink-0">
      {tabs.map(({ to, label, Icon }) => (
        <NavLink key={to} to={to} end style={{ textDecoration: 'none' }}>
          {({ isActive }) => (
            <div className="flex flex-col items-center gap-1 min-w-[56px]">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${isActive ? 'bg-blue-50' : ''}`}>
                <Icon size={20} color={isActive ? '#3b82f6' : '#aaa'} strokeWidth={isActive ? 2.5 : 1.8} />
              </div>
              <span className={`text-[11px] font-semibold ${isActive ? 'text-blue-500' : 'text-gray-400'}`}>
                {label}
              </span>
            </div>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
