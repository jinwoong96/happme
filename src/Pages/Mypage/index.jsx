import { useNavigate } from 'react-router-dom';
import { Bookmark, Bell, UserPen, Lock, Headphones, FileText, ChevronRight } from 'lucide-react';
import useMypage from '../../hooks/useMypage';

const MENU = [
  { Icon: Bookmark,   label: '즐겨찾기', path: '/bookmark' },
  { Icon: Bell,       label: '알림 설정' },
  { Icon: Bell,       label: '알림함', path: '/alerts' },
  { Icon: UserPen,    label: '프로필 수정', path: '/recommendation/profile', state: { from: 'mypage' } },
  { Icon: Lock,       label: '비밀번호 변경', path: '/mypage/password' },
  { Icon: Headphones, label: '고객센터', path: '/support' },
  { Icon: FileText,   label: '이용약관' },
];

export default function MypagePage() {
  const { user, handleLogout } = useMypage();
  const navigate = useNavigate();
  if (!user) return null;

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      <div className="bg-white" style={{ padding: '20px 20px 16px' }}>
        <p className="text-[22px] font-extrabold text-gray-900">마이</p>
      </div>

      {/* 프로필 카드 */}
      <div style={{ margin: '16px 20px 0', backgroundColor: '#fff', borderRadius: 20, padding: 20, boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 58, height: 58, borderRadius: '50%',
            background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 22, fontWeight: 700, flexShrink: 0,
          }}>
            {user.name[0]}
          </div>
          <div>
            <p className="text-[18px] font-bold text-gray-900">{user.name}</p>
            <p className="mt-0.5 text-[13px] text-gray-400">{user.email}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
          {[['즐겨찾기', user.bookmarkCount], ['신청 완료', 0], ['알림', 2]].map(([label, value]) => (
            <div key={label} style={{ flex: 1, backgroundColor: '#f8f9ff', borderRadius: 14, padding: '12px 8px', textAlign: 'center' }}>
              <p className="text-[20px] font-extrabold text-blue-500">{value}</p>
              <p className="mt-0.5 text-[11px] text-gray-400">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 메뉴 */}
      <div style={{ margin: '12px 20px 0', backgroundColor: '#fff', borderRadius: 20, overflow: 'hidden', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                {/* {MENU.map(({ Icon, label, path, state }, i) => (
          <button key={label}
            onClick={() => path && navigate(path, { state })} */}
        {MENU
          .filter(({ label }) => label !== '비밀번호 변경' || user.hasPassword)
          .map(({ Icon, label, path }, i, arr) => (
          <button key={label}
            onClick={path ? () => navigate(path) : undefined}  
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 14,
              padding: '16px 18px',
              backgroundColor: 'transparent', border: 'none', cursor: 'pointer', textAlign: 'left',
              borderBottom: i < arr.length - 1 ? '1px solid #f9fafb' : 'none',
            }}>
            <Icon size={18} color="#555" strokeWidth={1.8} />
            <span className="flex-1 text-[14px] text-gray-700 font-medium">{label}</span>
            <ChevronRight size={16} color="#ccc" />
          </button>
        ))}
      </div>

      {/* 로그아웃 */}
      <div style={{ margin: '12px 20px 24px' }}>
        <button onClick={handleLogout}
          style={{
            width: '100%', padding: '15px 0', borderRadius: 16,
            backgroundColor: '#fff', color: '#f87171', fontSize: 15, fontWeight: 700,
            border: '1px solid #fee2e2', cursor: 'pointer',
          }}>
          로그아웃
        </button>
      </div>
    </div>
  );
}