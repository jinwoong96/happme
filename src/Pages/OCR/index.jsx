import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ImageIcon, Bot, ChevronDown, ExternalLink, CheckCircle2, Loader2, X, Bookmark } from 'lucide-react';
import useOCR from '../../hooks/useOCR';
import useBookmarks from '../../hooks/useBookmarks';

function formatAge(min, max) {
  if (!min && !max) return '연령 제한 없음';
  if (min && max) return `${min}세 ~ ${max}세`;
  if (min) return `${min}세 이상`;
  return `${max}세 이하`;
}

function extractUrl(text) {
  if (!text) return null;
  const match = text.match(/(https?:\/\/[^\s)]+|www\.[^\s),]+)/i);
  if (!match) return null;
  const url = match[0];
  return url.startsWith('http') ? url : `https://${url}`;
}

function extractMaxAmount(text) {
  if (!text) return null;

  const regex = /(\d[\d,]*)\s*(억|천만|백만|만)?\s*원/g;
  const unit = { 억: 100000000, 천만: 10000000, 백만: 1000000, 만: 10000 };

  let max = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    const num = parseInt(match[1].replace(/,/g, ''), 10);
    if (Number.isNaN(num)) continue;
    const value = num * (unit[match[2]] || 1);
    if (value > max) max = value;
  }

  if (max === 0) return null;

  if (max >= 100000000) return `최대 ${Math.round(max / 100000000)}억원`;
  if (max >= 10000) return `최대 ${Math.round(max / 10000)}만원`;
  return `최대 ${max.toLocaleString()}원`;
}

function splitItems(text) {
  if (!text) return [];
  return text
    .split(/\r?\n|(?=[✅○●•·])/g)
    .map((s) => s.trim())
    .filter(Boolean);
}

function Field({ label, value, asList = false }) {
  const items = asList ? splitItems(value) : [];
  const isEmpty = asList ? items.length === 0 : !value;

  return (
    <div>
      <p style={{ fontSize: 13, fontWeight: 700, color: '#111827', margin: '0 0 4px' }}>{label}</p>
      {isEmpty ? (
        <p style={{ fontSize: 13, color: '#c1c5cb', margin: 0 }}>정보 없음</p>
      ) : asList ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {items.map((item, i) => (
            <p key={i} style={{ fontSize: 13, fontWeight: 400, color: '#6b7280', margin: 0, lineHeight: 1.5 }}>{item}</p>
          ))}
        </div>
      ) : (
        <p style={{ fontSize: 13, fontWeight: 400, color: '#6b7280', margin: 0, lineHeight: 1.5 }}>{value}</p>
      )}
    </div>
  );
}

function MatchAccordion({ match, isOpen, onToggle, isBookmarked, onToggleBookmark }) {
  const docs = splitItems(match.sbmsnDcmntCn);
  const maxAmount = extractMaxAmount(match.plcySprtCn);
  const effectiveUrl =
    match.aplyUrlAddr ||
    extractUrl(match.plcyAplyMthdCn) ||
    extractUrl(match.plcySprtCn) ||
    extractUrl(match.plcyExplnCn);

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 16, overflow: 'hidden', backgroundColor: '#fff' }}>
      <div
        role="button"
        tabIndex={0}
        onClick={onToggle}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggle(); }}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 16px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0 }}>
          <p style={{
            fontSize: 16, fontWeight: 800, color: '#111827', margin: 0,
            ...(isOpen ? {} : { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }),
          }}>
            {match.plcyNm}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {maxAmount && (
              <span style={{ fontSize: 11, fontWeight: 600, color: '#16a34a' }}>{maxAmount}</span>
            )}
            <span style={{ fontSize: 11, fontWeight: 600, color: '#3b82f6' }}>
              매칭도 {Math.round((match.score || 0) * 100)}%
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, marginLeft: 8 }}>
          <button
            onClick={(e) => { e.stopPropagation(); onToggleBookmark(match.policy_id); }}
            disabled={match.policy_id == null}
            className="bg-transparent border-none p-0.5"
            style={{ cursor: match.policy_id == null ? 'default' : 'pointer', display: 'flex' }}
            aria-label="즐겨찾기"
          >
            <Bookmark size={18} color={isBookmarked ? '#3b82f6' : '#ccc'} fill={isBookmarked ? '#3b82f6' : 'none'} />
          </button>
          <ChevronDown
            size={18}
            color="#9ca3af"
            style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
          />
        </div>
      </div>

      {isOpen && (
        <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ borderTop: '1px solid #f3f4f6', paddingTop: 12 }} />

          <Field label="정책 설명" value={match.plcyExplnCn} />
          <Field label="지원 대상" value={formatAge(match.sprtTrgtMinAge, match.sprtTrgtMaxAge)} />
          <Field label="지원 내용" value={match.plcySprtCn} asList />
          <Field label="신청 기간" value={match.aplyYmd} />
          <Field label="신청 방법" value={match.plcyAplyMthdCn} asList />

          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: '#111827', margin: '0 0 4px' }}>필요 서류</p>
            {docs.length === 0 ? (
              <p style={{ fontSize: 13, color: '#c1c5cb', margin: 0 }}>정보 없음</p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {docs.map((d, i) => <li key={i} style={{ fontSize: 13, fontWeight: 400, color: '#6b7280' }}>{d}</li>)}
              </ul>
            )}
          </div>

          {effectiveUrl ? (
            <a
              href={effectiveUrl}
              target="_blank"
              rel="noreferrer"
              style={{
                marginTop: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                padding: '10px 0', borderRadius: 12, backgroundColor: '#eff6ff', color: '#3b82f6',
                fontSize: 13, fontWeight: 700, textDecoration: 'none',
              }}
            >
              공식 사이트
              <ExternalLink size={14} />
            </a>
          ) : (
            <div style={{
              marginTop: 4, display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '10px 0', borderRadius: 12, backgroundColor: '#f9fafb', color: '#c1c5cb',
              fontSize: 13, fontWeight: 700,
            }}>
              공식 사이트 정보 없음
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function OCRPage() {
  const { files, loading, results, error, handleFileChange, handleRemoveFile, handleAnalyze } = useOCR();
  const { isBookmarked, toggleBookmark } = useBookmarks();
  const navigate = useNavigate();
  const can = !loading && files.length > 0;
  const [openIndex, setOpenIndex] = useState(0);
  const [previewUrl, setPreviewUrl] = useState(null);

  // 선택한 이미지 미리보기 URL 생성/해제
  useEffect(() => {
    if (files.length === 0) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(files[0]);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [files]);

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">공고문 사진 분석</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
        <div className="flex gap-3 bg-blue-50 rounded-2xl mb-5" style={{ padding: '14px 16px' }}>
          <div className="w-[34px] h-[34px] rounded-full bg-blue-500 flex items-center justify-center shrink-0">
            <Bot size={18} color="#fff" />
          </div>
          <p className="text-[13px] text-gray-600 leading-relaxed">현수막·포스터 사진을 올리면 AI가 관련 정책을 찾아드려요.</p>
        </div>

        <label style={{ display: 'block', position: 'relative', cursor: loading ? 'default' : 'pointer' }}>
          <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" disabled={loading} />
          <div style={{ border: '2px dashed #d1d5db', borderRadius: 24, padding: previewUrl ? '20px' : '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, backgroundColor: '#fff' }}>
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="업로드한 이미지 미리보기"
                style={{ width: '100%', maxHeight: 320, borderRadius: 18, objectFit: 'contain', border: '1px solid #e5e7eb', backgroundColor: '#f9fafb' }}
              />
            ) : (
              <div className="w-[60px] h-[60px] rounded-[18px] bg-blue-50 flex items-center justify-center">
                <ImageIcon size={28} color="#3b82f6" strokeWidth={1.5} />
              </div>
            )}
            {files.length === 0
              ? <p className="text-[13px] text-gray-400">이미지를 선택하세요</p>
              : <p className="text-[14px] font-semibold text-gray-800">{files[0].name}</p>
            }
          </div>

          {/* 업로드한 파일을 취소할 수 있는 X 버튼 */}
          {files.length > 0 && !loading && (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleRemoveFile();
              }}
              aria-label="업로드 취소"
              style={{
                position: 'absolute',
                top: 10,
                right: 10,
                width: 26,
                height: 26,
                borderRadius: '50%',
                border: 'none',
                backgroundColor: '#9ca3af',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              <X size={15} />
            </button>
          )}
        </label>

        <button onClick={handleAnalyze} disabled={!can}
          style={{
            marginTop: 14,
            width: '100%',
            padding: '16px 0',
            borderRadius: 16,
            background: can ? 'linear-gradient(135deg, #60a5fa, #3b82f6)' : '#e5e7eb',
            color: can ? '#fff' : '#9ca3af',
            fontSize: 16,
            fontWeight: 700,
            border: 'none',
            cursor: can ? 'pointer' : 'default',
            boxShadow: can ? '0 6px 18px rgba(59,130,246,0.38)' : 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
          {loading && <Loader2 size={16} className="animate-spin" />}
          {loading ? '분석 중...' : '이미지 분석 시작'}
        </button>

        {loading && (
          <p style={{ marginTop: 10, textAlign: 'center', fontSize: 12, color: '#9ca3af' }}>
            이미지 분석에는 최대 30초 정도 걸릴 수 있어요. 잠시만 기다려주세요.
          </p>
        )}

        {error && (
          <div style={{ marginTop: 14, padding: '12px 16px', borderRadius: 12, backgroundColor: '#fef2f2', color: '#dc2626', fontSize: 13 }}>
            {error}
          </div>
        )}

        {results && results.message && (
          <div style={{ marginTop: 14, padding: '12px 16px', borderRadius: 12, backgroundColor: '#fffbeb', color: '#b45309', fontSize: 13 }}>
            {results.message}
          </div>
        )}

        {results && results.matches.length > 0 && (
          <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={18} color="#22c55e" />
                <p className="text-[14px] font-bold text-gray-900">분석 완료 · 정책 {results.matches.length}건 매칭</p>
              </div>
              <button
                onClick={() => navigate('/bookmark')}
                style={{
                  display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
                  padding: '6px 10px', borderRadius: 999, border: 'none',
                  backgroundColor: '#eff6ff', color: '#3b82f6', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                }}
              >
                <Bookmark size={13} />
                즐겨찾기 보기
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {results.matches.map((m, i) => (
                <MatchAccordion
                  key={m.policy_id ?? i}
                  match={m}
                  isOpen={openIndex === i}
                  onToggle={() => setOpenIndex(openIndex === i ? -1 : i)}
                  isBookmarked={isBookmarked(m.policy_id)}
                  onToggleBookmark={toggleBookmark}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}