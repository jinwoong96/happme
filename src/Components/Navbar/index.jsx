import { NavLink } from 'react-router-dom';
import { Home, Grid2x2, Headphones, User } from 'lucide-react';

const tabs = [
  { to: '/', label: '홈', Icon: Home },
  { to: '/category', label: '카테고리', Icon: Grid2x2 },
  { to: '/support', label: '고객센터', Icon: Headphones },
  { to: '/mypage', label: '마이', Icon: User },
];

export default function Navbar() {
  return (
    <nav style={{
      display: 'flex', justifyContent: 'space-around', alignItems: 'center',
      background: '#fff',
      borderTop: '1px solid #f0f0f0',
      padding: '10px 0 12px',
      flexShrink: 0,
    }}>
      {tabs.map(({ to, label, Icon }) => (
        <NavLink key={to} to={to} end style={{ textDecoration: 'none' }}>
          {({ isActive }) => (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, minWidth: 56 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 12,
                background: isActive ? '#eff6ff' : 'transparent',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon size={20} color={isActive ? '#3b82f6' : '#aaa'} strokeWidth={isActive ? 2.5 : 1.8} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 600, color: isActive ? '#3b82f6' : '#aaa' }}>
                {label}
              </span>
            </div>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
