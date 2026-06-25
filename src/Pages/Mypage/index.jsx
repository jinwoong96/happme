import { Bookmark, Bell, UserPen, Lock, Headphones, FileText, ChevronRight } from 'lucide-react';
import useMypage from '../../hooks/useMypage';

const MENU_ITEMS = [
  { Icon: Bookmark, label: '즐겨찾기 목록' },
  { Icon: Bell, label: '알림 설정' },
  { Icon: UserPen, label: '프로필 수정' },
  { Icon: Lock, label: '비밀번호 변경' },
  { Icon: Headphones, label: '고객센터' },
  { Icon: FileText, label: '이용약관' },
];

export default function MypagePage() {
  const { user, handleLogout } = useMypage();
  if (!user) return null;

  return (
    <div style={{ background: '#f5f6fa' }}>
      <div style={{ padding: '20px 20px 16px', background: '#fff' }}>
        <p style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#111' }}>마이</p>
      </div>

      {/* 프로필 카드 */}
      <div style={{ margin: 16, background: '#fff', borderRadius: 20, padding: 20, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 58, height: 58, borderRadius: '50%', background: 'linear-gradient(135deg, #60a5fa, #3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 22, fontWeight: 700 }}>
            {user.name[0]}
          </div>
          <div>
            <p style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#111' }}>{user.name}</p>
            <p style={{ margin: '3px 0 0', fontSize: 13, color: '#aaa' }}>{user.email}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
          {[{ label: '즐겨찾기', value: user.bookmarkCount }, { label: '신청 완료', value: 0 }, { label: '알림', value: 2 }].map(({ label, value }) => (
            <div key={label} style={{ flex: 1, background: '#f8f9ff', borderRadius: 14, padding: '12px 8px', textAlign: 'center' }}>
              <p style={{ margin: 0, fontSize: 20, fontWeight: 800, color: '#3b82f6' }}>{value}</p>
              <p style={{ margin: '3px 0 0', fontSize: 11, color: '#aaa' }}>{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 메뉴 */}
      <div style={{ margin: '0 16px 16px', background: '#fff', borderRadius: 20, overflow: 'hidden', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
        {MENU_ITEMS.map(({ Icon, label }, i) => (
          <button key={label} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: '16px 18px', background: 'none', border: 'none', borderBottom: i < MENU_ITEMS.length - 1 ? '1px solid #f5f5f5' : 'none', cursor: 'pointer', textAlign: 'left' }}>
            <Icon size={18} color="#555" strokeWidth={1.8} />
            <span style={{ fontSize: 14, color: '#333', fontWeight: 500, flex: 1 }}>{label}</span>
            <ChevronRight size={16} color="#ccc" />
          </button>
        ))}
      </div>

      {/* 로그아웃 */}
      <div style={{ margin: '0 16px 24px' }}>
        <button onClick={handleLogout} style={{ width: '100%', padding: 15, borderRadius: 16, background: '#fff', color: '#f87171', fontSize: 15, fontWeight: 700, border: '1.5px solid #fee2e2', cursor: 'pointer' }}>
          로그아웃
        </button>
      </div>
    </div>
  );
}
