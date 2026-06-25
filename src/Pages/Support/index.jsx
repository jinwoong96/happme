import { User, HelpCircle, Megaphone, Building2, ChevronRight } from 'lucide-react';
import useSupport from '../../hooks/useSupport';

const CATS = [
  { Icon: User,       bg: '#eff6ff', color: '#3b82f6', title: '사용자 문의',         desc: '서비스 이용 관련 문의' },
  { Icon: HelpCircle, bg: '#fffbeb', color: '#f59e0b', title: '기타 문의',           desc: '일반 문의 및 건의사항' },
  { Icon: Megaphone,  bg: '#fdf2f8', color: '#ec4899', title: '광고제휴 문의',       desc: '광고 및 마케팅 제휴 신청' },
  { Icon: Building2,  bg: '#f0fdf4', color: '#22c55e', title: '기업지원금 제휴 문의', desc: '기업 지원금 등록 및 제휴' },
];

export default function SupportPage() {
  const { handleContact } = useSupport();

  return (
    <div style={{ backgroundColor: '#f5f6fa' }}>
      <div className="bg-white" style={{ padding: '20px 20px 16px' }}>
        <p className="text-[22px] font-extrabold text-gray-900">고객센터</p>
        <p className="mt-1.5 text-[13px] text-gray-400">문의 유형을 선택해 주세요</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '16px 20px 12px' }}>
        {CATS.map(({ Icon, bg, color, title, desc }) => (
          <button key={title} onClick={() => handleContact(title)}
            style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '18px 18px',
              backgroundColor: '#fff',
              borderRadius: 18,
              border: 'none', cursor: 'pointer', textAlign: 'left',
              boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
            }}>
            <div style={{ width: 48, height: 48, borderRadius: 16, backgroundColor: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Icon size={22} color={color} strokeWidth={1.8} />
            </div>
            <div style={{ flex: 1 }}>
              <p className="text-[15px] font-bold text-gray-900">{title}</p>
              <p className="mt-0.5 text-[12px] text-gray-400">{desc}</p>
            </div>
            <ChevronRight size={18} color="#ccc" />
          </button>
        ))}
      </div>

      <div style={{ margin: '0 20px 24px', backgroundColor: '#fff', borderRadius: 18, padding: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
        <p className="mb-2.5 text-[13px] font-bold text-gray-700">운영 안내</p>
        {[['운영시간','평일 09:00 ~ 18:00'],['점심시간','12:00 ~ 13:00'],['이메일','support@benefix.kr']].map(([l,v]) => (
          <div key={l} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span className="text-[12px] text-gray-400">{l}</span>
            <span className="text-[12px] text-gray-600 font-medium">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
