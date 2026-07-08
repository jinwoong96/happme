import { User, HelpCircle, Megaphone, Building2 } from 'lucide-react';

export const INQUIRY_TYPES = {
  user: {
    title: '사용자 문의',
    desc: '서비스 이용 관련 문의',
    Icon: User,
    bg: '#eff6ff',
    color: '#3b82f6',
    endpoint: '/inquiries/',
    buildBody: (form) => ({ inquiry_type: '사용자 문의', title: form.title, content: form.content }),
    fields: [
      { name: 'title', label: '제목', type: 'text', placeholder: '제목을 입력하세요' },
      { name: 'content', label: '내용', type: 'textarea', placeholder: '문의 내용을 입력하세요' },
    ],
  },
  general: {
    title: '기타 문의',
    desc: '일반 문의 및 건의사항',
    Icon: HelpCircle,
    bg: '#fffbeb',
    color: '#f59e0b',
    endpoint: '/inquiries/',
    buildBody: (form) => ({ inquiry_type: '기타 문의', title: form.title, content: form.content }),
    fields: [
      { name: 'title', label: '제목', type: 'text', placeholder: '제목을 입력하세요' },
      { name: 'content', label: '내용', type: 'textarea', placeholder: '문의 내용을 입력하세요' },
    ],
  },
  ad: {
    title: '광고제휴 문의',
    desc: '광고 및 마케팅 제휴 신청',
    Icon: Megaphone,
    bg: '#fdf2f8',
    color: '#ec4899',
    endpoint: '/ad-partnership-inquiries/',
    buildBody: (form) => form,
    fields: [
      { name: 'ad_name', label: '광고명', type: 'text', placeholder: '광고명을 입력하세요' },
      { name: 'company_name', label: '기업명', type: 'text', placeholder: '기업명을 입력하세요' },
      { name: 'target_product', label: '광고 대상 상품/서비스명', type: 'text', placeholder: '광고 대상 상품 또는 서비스명을 입력하세요' },
      { name: 'content', label: '광고 내용', type: 'textarea', placeholder: '광고 내용을 입력하세요' },
    ],
  },
  corporate: {
    title: '기업지원금 제휴 문의',
    desc: '기업 지원금 등록 및 제휴',
    Icon: Building2,
    bg: '#f0fdf4',
    color: '#22c55e',
    endpoint: '/corporate-support-inquiries/',
    buildBody: (form) => form,
    fields: [
      { name: 'company_name', label: '기업명', type: 'text', placeholder: '기업명을 입력하세요' },
      { name: 'support_content', label: '지원금 내용', type: 'textarea', placeholder: '광고 내용, 예산, 기간 등을 입력해주세요' },
      { name: 'support_period', label: '지원금 기간', type: 'text', placeholder: '예: 2026-01-01 ~ 2026-06-30' },
    ],
  },
};
