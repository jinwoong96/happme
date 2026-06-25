import { User, HelpCircle, Megaphone, Building2, ChevronRight } from 'lucide-react';
import useSupport from '../../hooks/useSupport';

const CATEGORIES = [
  {
    Icon: User,
    iconBg: '#eff6ff', iconColor: '#3b82f6',
    title: '사용자 문의',
    desc: '서비스 이용 관련 문의',
  },
  {
    Icon: HelpCircle,
    iconBg: '#fef9ee', iconColor: '#f59e0b',
    title: '기타 문의',
    desc: '일반 문의 및 건의사항',
  },
  {
    Icon: Megaphone,
    iconBg: '#fdf2f8', iconColor: '#ec4899',
    title: '광고제휴 문의',
    desc: '광고 및 마케팅 제휴 신청',
  },
  {
    Icon: Building2,
    iconBg: '#f0fdf4', iconColor: '#22c55e',
    title: '기업지원금 제휴 문의',
    desc: '기업 지원금 등록 및 제휴',
  },
];

export default function SupportPage() {
  const { handleContact } = useSupport();

  return (
    <div style={{ background: '#f5f6fa' }}>
      {/* 헤더 */}
      <div style={{ padding: '20px 20px 16px', background: '#fff' }}>
        <p style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#111' }}>고객센터</p>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: '#aaa' }}>문의 유형을 선택해 주세요</p>
      </div>

      {/* 카테고리 카드 */}
      <div style={{ padding: '16px 16px 0', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {CATEGORIES.map(({ Icon, iconBg, iconColor, title, desc }) => (
          <button
            key={title}
            onClick={() => handleContact(title)}
            style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '18px 18px',
              background: '#fff', borderRadius: 18,
              border: 'none', cursor: 'pointer', textAlign: 'left',
              boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
            }}
          >
            <div style={{
              width: 48, height: 48, borderRadius: 16,
              background: iconBg,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <Icon size={22} color={iconColor} strokeWidth={1.8} />
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#111' }}>{title}</p>
              <p style={{ margin: '3px 0 0', fontSize: 12, color: '#aaa' }}>{desc}</p>
            </div>
            <ChevronRight size={18} color="#ccc" />
          </button>
        ))}
      </div>

      {/* 운영시간 안내 */}
      <div style={{ margin: '16px 16px 24px', background: '#fff', borderRadius: 18, padding: '18px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
        <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 700, color: '#333' }}>운영 안내</p>
        {[
          { label: '운영시간', value: '평일 09:00 ~ 18:00' },
          { label: '점심시간', value: '12:00 ~ 13:00' },
          { label: '이메일', value: 'support@benefix.kr' },
        ].map(({ label, value }) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: '#aaa' }}>{label}</span>
            <span style={{ fontSize: 12, color: '#555', fontWeight: 500 }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
