import { User, HelpCircle, Megaphone, Building2, ChevronRight } from 'lucide-react';
import useSupport from '../../hooks/useSupport';

const CATEGORIES = [
  { Icon: User,      iconBg: 'bg-blue-50',   iconColor: '#3b82f6', title: '사용자 문의',       desc: '서비스 이용 관련 문의' },
  { Icon: HelpCircle, iconBg: 'bg-amber-50',  iconColor: '#f59e0b', title: '기타 문의',         desc: '일반 문의 및 건의사항' },
  { Icon: Megaphone,  iconBg: 'bg-pink-50',   iconColor: '#ec4899', title: '광고제휴 문의',     desc: '광고 및 마케팅 제휴 신청' },
  { Icon: Building2,  iconBg: 'bg-green-50',  iconColor: '#22c55e', title: '기업지원금 제휴 문의', desc: '기업 지원금 등록 및 제휴' },
];

const INFO = [
  { label: '운영시간', value: '평일 09:00 ~ 18:00' },
  { label: '점심시간', value: '12:00 ~ 13:00' },
  { label: '이메일',   value: 'support@benefix.kr' },
];

export default function SupportPage() {
  const { handleContact } = useSupport();

  return (
    <div className="bg-[#f5f6fa]">
      <div className="px-5 pt-5 pb-4 bg-white">
        <p className="m-0 text-[22px] font-extrabold text-[#111]">고객센터</p>
        <p className="m-0 mt-1.5 text-[13px] text-[#aaa]">문의 유형을 선택해 주세요</p>
      </div>

      <div className="px-4 pt-4 flex flex-col gap-3">
        {CATEGORIES.map(({ Icon, iconBg, iconColor, title, desc }) => (
          <button
            key={title}
            onClick={() => handleContact(title)}
            className="flex items-center gap-4 px-[18px] py-[18px] bg-white rounded-[18px] border-none cursor-pointer text-left shadow-[0_2px_10px_rgba(0,0,0,0.05)]"
          >
            <div className={`w-12 h-12 rounded-[16px] ${iconBg} flex items-center justify-center shrink-0`}>
              <Icon size={22} color={iconColor} strokeWidth={1.8} />
            </div>
            <div className="flex-1">
              <p className="m-0 text-[15px] font-bold text-[#111]">{title}</p>
              <p className="m-0 mt-0.5 text-[12px] text-[#aaa]">{desc}</p>
            </div>
            <ChevronRight size={18} color="#ccc" />
          </button>
        ))}
      </div>

      {/* 운영 안내 */}
      <div className="mx-4 mt-3 mb-6 bg-white rounded-[18px] p-[18px] shadow-[0_2px_10px_rgba(0,0,0,0.05)]">
        <p className="m-0 mb-2.5 text-[13px] font-bold text-[#333]">운영 안내</p>
        {INFO.map(({ label, value }) => (
          <div key={label} className="flex justify-between mb-1.5">
            <span className="text-[12px] text-[#aaa]">{label}</span>
            <span className="text-[12px] text-[#555] font-medium">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
