import { useNavigate } from 'react-router-dom';
import { Users, Megaphone, MessageSquareText, LogOut, ChevronRight } from 'lucide-react';
import { api } from '../../utils/api';

const MENU = [
  { Icon: Users, label: '회원 관리', desc: '회원 목록 조회 및 삭제', path: '/admin/members' },
  { Icon: Megaphone, label: '공지 · 알림 발송', desc: '전체 회원에게 공지사항 알림 발송', path: '/admin/notify' },
  { Icon: MessageSquareText, label: '문의 관리', desc: '고객센터 문의 답변', path: '/admin/inquiries' },
];

export default function AdminPage() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.post('/users/logout');
    } catch {
      // 쿠키가 이미 만료된 경우 등은 무시하고 로그인 화면으로 이동
    }
    localStorage.clear();
    navigate('/login');
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%' }}>
      <div className="bg-white flex items-center justify-between" style={{ padding: '20px 20px 16px' }}>
        <div>
          <p className="text-[22px] font-extrabold text-gray-900">관리자</p>
          <p className="mt-1 text-[13px] text-gray-400">서비스 운영 관리</p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1 bg-transparent border-none cursor-pointer"
          style={{ color: '#f87171', fontSize: 13, fontWeight: 700 }}
        >
          <LogOut size={16} />
          로그아웃
        </button>
      </div>

      <div className="flex flex-col" style={{ gap: 12, padding: '16px 20px 24px' }}>
        {MENU.map(({ Icon, label, desc, path }) => (
          <button
            key={path}
            onClick={() => navigate(path)}
            style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '18px 18px', backgroundColor: '#fff', borderRadius: 18,
              border: 'none', cursor: 'pointer', textAlign: 'left',
              boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
            }}
          >
            <div style={{ width: 48, height: 48, borderRadius: 16, backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Icon size={22} color="#3b82f6" strokeWidth={1.8} />
            </div>
            <div style={{ flex: 1 }}>
              <p className="text-[15px] font-bold text-gray-900">{label}</p>
              <p className="mt-0.5 text-[12px] text-gray-400">{desc}</p>
            </div>
            <ChevronRight size={18} color="#ccc" />
          </button>
        ))}
      </div>
    </div>
  );
}
