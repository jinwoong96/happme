import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronUp, UserPen } from 'lucide-react';
import useRecommendationProfile from '../../hooks/useRecommendationProfile';
import { ToggleGroup } from '../../Components/ChoiceButtons';
import { REGIONS } from '../../data/regions';
import {
  GENDER_OPTIONS,
  MARITAL_OPTIONS,
  EMPLOYMENT_OPTIONS,
  EDUCATION_OPTIONS,
  MAJOR_CATEGORY_OPTIONS,
  STUDENT_STATUS_OPTIONS,
  STARTUP_STATUS_OPTIONS,
  HOUSING_OPTIONS,
  COMPANY_TYPE_OPTIONS,
  YES_NO_OPTIONS,
} from '../../data/codeOptions';

const labelStyle = { margin: '0 0 7px', fontSize: 13, fontWeight: 600, color: '#374151' };
const sectionTitleStyle = { margin: '28px 0 14px', fontSize: 15, fontWeight: 700, color: '#111827' };

const inputStyle = {
  width: '100%',
  boxSizing: 'border-box',
  padding: '14px 16px',
  borderRadius: 14,
  border: '1.5px solid #e5e7eb',
  fontSize: 14,
  backgroundColor: '#fff',
  outline: 'none',
  color: '#1f2937',
};

function Field({ label, required, children }) {
  return (
    <div>
      <p style={labelStyle}>
        {label}
        {required && <span style={{ color: '#ef4444' }}> *</span>}
      </p>
      {children}
    </div>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select value={value || ''} onChange={(e) => onChange(e.target.value)} style={{ ...inputStyle, appearance: 'auto' }}>
      <option value="">선택하세요</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function TextInput({ value, onChange, placeholder, type = 'text' }) {
  return (
    <input
      type={type}
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={inputStyle}
    />
  );
}

// 숫자만 입력받아 "YYYY-MM-DD"로 자동 정렬해주는 생년월일 입력. 달력 UI 대신 키보드로만 입력하고 싶다는 요청 반영.
function formatBirthDateInput(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 8);
  const parts = [digits.slice(0, 4), digits.slice(4, 6), digits.slice(6, 8)].filter(Boolean);
  return parts.join('-');
}

// 아직 다 입력하지 않은 중간 상태("1999-01")는 에러로 취급하지 않고, 8자리를 다 채웠을 때만 판단한다.
function getBirthDateError(value) {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  const isRealDate = date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
  if (!isRealDate) return '실제 존재하지 않는 날짜입니다.';
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (date > today) return '미래 날짜는 입력할 수 없습니다.';
  return null;
}

function BirthDateInput({ value, onChange }) {
  const error = getBirthDateError(value);
  return (
    <div>
      <input
        type="text"
        inputMode="numeric"
        value={value ?? ''}
        onChange={(e) => onChange(formatBirthDateInput(e.target.value))}
        placeholder="YYYY-MM-DD (예: 19990101)"
        maxLength={10}
        style={{ ...inputStyle, border: error ? '1.5px solid #ef4444' : inputStyle.border }}
      />
      {error && <p style={{ margin: '6px 0 0', fontSize: 12, color: '#ef4444' }}>{error}</p>}
    </div>
  );
}

function Textarea({ value, onChange, placeholder }) {
  return (
    <textarea
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={3}
      style={{ ...inputStyle, resize: 'none', lineHeight: 1.5, fontFamily: 'inherit' }}
    />
  );
}

export default function RecommendationProfilePage() {
  const navigate = useNavigate();
  const { form, handleChange, handleSubmit, handleSkip, loading, saving, error, from, hasProfile } = useRecommendationProfile();
  const scrollRef = useRef(null);
  const [showScrollTop, setShowScrollTop] = useState(false);

  const handleScroll = (e) => {
    setShowScrollTop(e.target.scrollTop > 200);
  };

  const scrollToTop = () => {
    scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p className="text-[13px] text-gray-400">불러오는 중...</p>
      </div>
    );
  }

  const set = (field) => (value) => handleChange(field, value);

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="flex-1 text-[20px] font-bold text-gray-900">{from === 'mypage' ? '프로필 수정' : '맞춤형 지원금 추천'}</p>
        {from === 'recommendation' && hasProfile && (
          <button
            type="button"
            onClick={handleSkip}
            disabled={saving}
            className="bg-transparent border-none p-0"
            style={{ fontSize: 13, fontWeight: 600, color: '#9ca3af', cursor: saving ? 'default' : 'pointer' }}
          >
            건너뛰기
          </button>
        )}
      </div>

      <div ref={scrollRef} onScroll={handleScroll} style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <UserPen size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">정보를 입력하면 AI가 최적의 지원금을 추천해 드립니다.</p>
        </div>

        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Field label="생년월일" required>
            <BirthDateInput value={form.birth_date} onChange={set('birth_date')} />
          </Field>

          <Field label="성별" required>
            <ToggleGroup options={GENDER_OPTIONS} value={form.gender} onChange={set('gender')} />
          </Field>

          <Field label="거주 지역 (시/도)" required>
            <Select value={form.region} onChange={set('region')} options={REGIONS.map((r) => ({ value: r.name, label: r.name }))} />
          </Field>

          <Field label="거주 지역 (시/군/구)">
            <TextInput value={form.district} onChange={set('district')} placeholder="예: 강남구" />
          </Field>

          <p style={sectionTitleStyle}>학력 정보</p>

          <Field label="최종 학력" required>
            <Select value={form.education} onChange={set('education')} options={EDUCATION_OPTIONS} />
          </Field>
          <Field label="학교명">
            <TextInput value={form.school_name} onChange={set('school_name')} placeholder="예: 한국대학교" />
          </Field>
          <Field label="전공">
            <TextInput value={form.major} onChange={set('major')} placeholder="예: 컴퓨터공학과" />
          </Field>
          <Field label="전공계열">
            <Select value={form.major_category} onChange={set('major_category')} options={MAJOR_CATEGORY_OPTIONS} />
          </Field>
          <Field label="재학 상태">
            <Select value={form.student_status} onChange={set('student_status')} options={STUDENT_STATUS_OPTIONS} />
          </Field>
          <Field label="졸업 연도">
            <TextInput type="number" value={form.graduation_year} onChange={set('graduation_year')} placeholder="예: 2024" />
          </Field>

          <p style={sectionTitleStyle}>취업/직업 정보</p>

          <Field label="취업상태" required>
            <Select value={form.employment_status} onChange={set('employment_status')} options={EMPLOYMENT_OPTIONS} />
          </Field>
          <Field label="직업/업종">
            <TextInput value={form.occupation} onChange={set('occupation')} placeholder="예: 농업인, 창업자 등" />
          </Field>
          <Field label="구직 여부">
            <ToggleGroup options={YES_NO_OPTIONS} value={form.job_seeking} onChange={set('job_seeking')} />
          </Field>
          <Field label="경력 사항">
            <Textarea value={form.career_history} onChange={set('career_history')} placeholder="주요 경력을 입력해주세요" />
          </Field>

          <p style={sectionTitleStyle}>혼인/특수 상태</p>

          <Field label="혼인상태" required>
            <Select value={form.marital_status} onChange={set('marital_status')} options={MARITAL_OPTIONS} />
          </Field>
          <Field label="기초생활수급자 여부">
            <ToggleGroup options={YES_NO_OPTIONS} value={form.basic_livelihood} onChange={set('basic_livelihood')} />
          </Field>
          <Field label="한부모가정 여부">
            <ToggleGroup options={YES_NO_OPTIONS} value={form.single_parent} onChange={set('single_parent')} />
          </Field>
          <Field label="장애 여부">
            <ToggleGroup options={YES_NO_OPTIONS} value={form.disability} onChange={set('disability')} />
          </Field>

          <p style={sectionTitleStyle}>창업 정보</p>

          <Field label="창업 관심 여부">
            <ToggleGroup options={YES_NO_OPTIONS} value={form.startup_interest} onChange={set('startup_interest')} />
          </Field>
          <Field label="사업자 여부">
            <ToggleGroup options={YES_NO_OPTIONS} value={form.business_owner} onChange={set('business_owner')} />
          </Field>
          <Field label="창업 단계">
            <Select value={form.startup_status} onChange={set('startup_status')} options={STARTUP_STATUS_OPTIONS} />
          </Field>
          <Field label="기업 형태">
            <Select value={form.company_type} onChange={set('company_type')} options={COMPANY_TYPE_OPTIONS} />
          </Field>

          <p style={sectionTitleStyle}>기타</p>

          <Field label="주거 상태">
            <Select value={form.housing_status} onChange={set('housing_status')} options={HOUSING_OPTIONS} />
          </Field>
          <Field label="현재 상황">
            <Textarea value={form.situation} onChange={set('situation')} placeholder="현재 상황을 자유롭게 입력해주세요" />
          </Field>
          <Field label="기타 참고 사항">
            <Textarea value={form.reason} onChange={set('reason')} placeholder="추가로 참고할 내용이 있다면 입력해주세요" />
          </Field>

          {error && <p style={{ margin: 0, fontSize: 13, color: '#ef4444', textAlign: 'center' }}>{error}</p>}

          <button
            type="submit"
            disabled={saving}
            style={{
              marginTop: 4,
              width: '100%',
              padding: '16px 0',
              borderRadius: 16,
              background: saving ? '#e5e7eb' : 'linear-gradient(135deg, #60a5fa, #3b82f6)',
              color: saving ? '#9ca3af' : '#fff',
              fontSize: 16,
              fontWeight: 700,
              border: 'none',
              cursor: saving ? 'default' : 'pointer',
              boxShadow: saving ? 'none' : '0 6px 18px rgba(59,130,246,0.38)',
            }}
          >
            {saving ? '저장 중...' : from === 'mypage' ? '수정 완료' : '다음'}
          </button>
        </form>
      </div>

      {showScrollTop && (
        <button
          onClick={scrollToTop}
          style={{
            position: 'absolute', right: 20, bottom: 20, width: 44, height: 44,
            borderRadius: '50%', border: 'none', backgroundColor: '#3b82f6', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(59,130,246,0.4)',
          }}
        >
          <ChevronUp size={22} />
        </button>
      )}
    </div>
  );
}
