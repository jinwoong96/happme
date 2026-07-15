import { Bookmark, ExternalLink, Users, CalendarClock, ClipboardList, FileText, Wallet, Info, Link2 } from 'lucide-react';
import Modal from '../Modal';

function formatWon(amount) {
  if (amount == null) return null;
  if (amount >= 100_000_000) {
    const eok = amount / 100_000_000;
    return `최대 ${Number.isInteger(eok) ? eok : eok.toFixed(1)}억원`;
  }
  if (amount >= 10_000) {
    return `최대 ${Math.round(amount / 10_000).toLocaleString()}만원`;
  }
  return `최대 ${amount.toLocaleString()}원`;
}

function formatYmd(raw) {
  const trimmed = (raw || '').trim();
  if (trimmed.length !== 8) return trimmed || null;
  return `${trimmed.slice(0, 4)}.${trimmed.slice(4, 6)}.${trimmed.slice(6, 8)}`;
}

function formatYmdRange(text) {
  if (!text) return null;
  return text.split('~').map((part) => formatYmd(part)).join(' ~ ');
}

// 카드(policy_cards.json) 데이터가 있으면 그걸 우선 쓰고, 없으면 원본 필드로 대체한다.
function getApplyPeriodText(p) {
  if (p.apply_period_type === '상시') return '상시';
  if (p.apply_period) return p.apply_period;
  const raw = formatYmdRange(p.aplyYmd);
  if (raw) return raw;
  return p.bizPrdEtcCn || null;
}

function getDeadlineBadge(aplyEndDt) {
  if (!aplyEndDt) return null;
  const end = new Date(aplyEndDt);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { label: '마감', bg: '#f3f4f6', color: '#9ca3af' };
  if (diffDays <= 7) return { label: `D-${diffDays}`, bg: '#fee2e2', color: '#dc2626' };
  if (diffDays <= 30) return { label: `D-${diffDays}`, bg: '#ffedd5', color: '#ea580c' };
  return { label: `D-${diffDays}`, bg: '#dbeafe', color: '#2563eb' };
}

function getIncomeText(p) {
  if (p.earnEtcCn) return p.earnEtcCn;
  if (p.earnMaxAmt) {
    if (p.earnMinAmt) return `연소득 ${p.earnMinAmt.toLocaleString()}만원 ~ ${p.earnMaxAmt.toLocaleString()}만원`;
    return `연소득 ${p.earnMaxAmt.toLocaleString()}만원 이하`;
  }
  return null;
}

function getBizPeriodText(p) {
  const begin = formatYmd(p.bizPrdBgngYmd);
  const end = formatYmd(p.bizPrdEndYmd);
  if (begin && end) return `${begin} ~ ${end}`;
  return p.bizPrdEtcCn || null;
}

function Section({ icon: Icon, title, children }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1.5">
        <Icon size={14} color="#3b82f6" />
        <p className="text-[13px] font-bold text-gray-800">{title}</p>
      </div>
      <div className="text-[12.5px] text-gray-600" style={{ lineHeight: 1.6, whiteSpace: 'pre-line', paddingLeft: 20 }}>
        {children}
      </div>
    </div>
  );
}

export default function PolicyDetailModal({ selectedPolicy, policyLoading, isBookmarked, onToggleBookmark, bookmarkDisabled, onClose }) {
  const p = selectedPolicy;
  const deadlineBadge = p && !p.error ? getDeadlineBadge(p.aplyEndDt) : null;
  const applyPeriodText = p && !p.error ? getApplyPeriodText(p) : null;
  const incomeText = p && !p.error ? getIncomeText(p) : null;
  const bizPeriodText = p && !p.error ? getBizPeriodText(p) : null;
  const maxAmountText = p && !p.error ? formatWon(p.maxSprtAmt) : null;

  return (
    <Modal isOpen={!!p} onClose={onClose} title={p?.plcyNm} maxWidth={340} maxHeight="82%">
      {p && (
        <div className="flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <button
              onClick={() => onToggleBookmark(p.policy_id)}
              disabled={bookmarkDisabled || p.policy_id == null}
              className="flex items-center gap-1.5 bg-transparent border-none p-0 self-start"
              style={{ cursor: bookmarkDisabled || p.policy_id == null ? 'default' : 'pointer' }}
            >
              <Bookmark
                size={18}
                color={isBookmarked ? '#3b82f6' : '#9ca3af'}
                fill={isBookmarked ? '#3b82f6' : 'none'}
              />
              <span className="text-[13px] font-semibold" style={{ color: isBookmarked ? '#3b82f6' : '#6b7280' }}>
                {isBookmarked ? '즐겨찾기' : '즐겨찾기 추가'}
              </span>
            </button>
            {deadlineBadge && (
              <span
                className="text-[11px] font-bold"
                style={{ padding: '3px 9px', borderRadius: 999, background: deadlineBadge.bg, color: deadlineBadge.color }}
              >
                {deadlineBadge.label}
              </span>
            )}
          </div>

          {policyLoading ? (
            <p className="text-[13px] text-gray-400">불러오는 중...</p>
          ) : p.error ? (
            <p className="text-[13px] text-red-400">{p.error}</p>
          ) : (
            <>
              {(p.rgtrInstCdNm || p.lclsfNm) && (
                <div className="flex items-center gap-1.5 flex-wrap" style={{ marginTop: -8 }}>
                  {p.lclsfNm && (
                    <span className="text-[11px] font-medium" style={{ padding: '3px 8px', borderRadius: 8, background: '#f3f4f6', color: '#6b7280' }}>
                      {p.lclsfNm}
                    </span>
                  )}
                  {p.rgtrInstCdNm && <span className="text-[11.5px] text-gray-400">{p.rgtrInstCdNm}</span>}
                </div>
              )}

              {p.policy_summary && (
                <div style={{ background: '#eff6ff', borderRadius: 14, padding: '14px 14px' }}>
                  <p className="text-[12px] font-bold text-blue-600 mb-1">한눈에 보기</p>
                  <p className="text-[13px] text-gray-700" style={{ lineHeight: 1.6 }}>{p.policy_summary}</p>
                  {(maxAmountText || applyPeriodText) && (
                    <div className="flex gap-4" style={{ marginTop: 10 }}>
                      {maxAmountText && (
                        <div>
                          <p className="text-[10.5px] text-gray-400">지원 금액</p>
                          <p className="text-[13px] font-bold text-gray-800">{maxAmountText}</p>
                        </div>
                      )}
                      {applyPeriodText && (
                        <div>
                          <p className="text-[10.5px] text-gray-400">신청 기간</p>
                          <p className="text-[13px] font-bold text-gray-800">{applyPeriodText}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {p.plcyExplnCn && (
                <Section icon={Info} title="정책 소개">
                  {p.plcyExplnCn}
                </Section>
              )}

              {p.plcySprtCn && (
                <Section icon={Wallet} title="지원 내용">
                  {p.plcySprtCn}
                </Section>
              )}

              {(p.sprtTrgtMinAge != null || p.target || p.ptcpPrpTrgtCn || p.addAplyQlfcCndCn || incomeText) && (
                <Section icon={Users} title="지원 대상">
                  {p.sprtTrgtMaxAge === 0 ? (
                    <p>연령 제한 없음</p>
                  ) : (p.sprtTrgtMinAge != null || p.sprtTrgtMaxAge != null) && (
                    <p>만 {p.sprtTrgtMinAge}세 ~ {p.sprtTrgtMaxAge}세</p>
                  )}
                  {incomeText && <p>{incomeText}</p>}
                  {p.ptcpPrpTrgtCn && <p style={{ marginTop: 4 }}>{p.ptcpPrpTrgtCn}</p>}
                  {p.addAplyQlfcCndCn && <p style={{ marginTop: 4 }}>{p.addAplyQlfcCndCn}</p>}
                </Section>
              )}

              {(applyPeriodText || p.plcyAplyMthdCn || p.srngMthdCn || p.sbmsnDcmntCn) && (
                <Section icon={CalendarClock} title="신청 안내">
                  {applyPeriodText && <p>신청 기간: {applyPeriodText}</p>}
                  {p.plcyAplyMthdCn && <p style={{ marginTop: 4 }}>신청 방법: {p.plcyAplyMthdCn}</p>}
                  {p.srngMthdCn && <p style={{ marginTop: 4 }}>심사 방법: {p.srngMthdCn}</p>}
                  {p.sbmsnDcmntCn && <p style={{ marginTop: 4 }}>제출 서류: {p.sbmsnDcmntCn}</p>}
                </Section>
              )}

              {(bizPeriodText || p.sprtSclCnt || p.operInstCdNm) && (
                <Section icon={ClipboardList} title="사업 정보">
                  {bizPeriodText && <p>사업 기간: {bizPeriodText}</p>}
                  {!!p.sprtSclCnt && <p style={{ marginTop: 4 }}>지원 규모: {p.sprtSclCnt.toLocaleString()}명</p>}
                  {p.operInstCdNm && <p style={{ marginTop: 4 }}>운영 기관: {p.operInstCdNm}</p>}
                </Section>
              )}

              {p.etcMttrCn && (
                <Section icon={FileText} title="기타사항">
                  {p.etcMttrCn}
                </Section>
              )}

              {(p.aplyUrlAddr || p.refUrlAddr1 || p.refUrlAddr2) && (
                <div className="flex flex-col gap-2">
                  {p.aplyUrlAddr && (
                    <a
                      href={p.aplyUrlAddr}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-center gap-1.5"
                      style={{
                        padding: '12px 0', borderRadius: 12, background: '#3b82f6',
                        color: '#fff', fontSize: 14, fontWeight: 700, textDecoration: 'none',
                      }}
                    >
                      신청 바로가기 <ExternalLink size={15} />
                    </a>
                  )}
                  {(p.refUrlAddr1 || p.refUrlAddr2) && (
                    <div className="flex gap-2">
                      {[p.refUrlAddr1, p.refUrlAddr2].filter(Boolean).map((url, i, arr) => (
                        <a
                          key={url}
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-center gap-1"
                          style={{
                            flex: 1, padding: '10px 0', borderRadius: 12, border: '1px solid #e5e7eb',
                            color: '#6b7280', fontSize: 12.5, fontWeight: 600, textDecoration: 'none',
                          }}
                        >
                          <Link2 size={13} /> 참고 링크{arr.length > 1 ? ` ${i + 1}` : ''}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </Modal>
  );
}
