import { Bookmark } from 'lucide-react';

export default function PolicyCard({ policy, badge, onOpen, isBookmarked, onToggleBookmark, bookmarkDisabled, onCheckIncome, children }) {
  return (
    <div
      onClick={() => onOpen(policy.policy_id, policy.policy_name, isBookmarked)}
      style={{ cursor: 'pointer', backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}
    >
      <div className="flex justify-between items-start gap-2">
        <p className="text-[15px] font-bold text-gray-900">{policy.policy_name}</p>
        <button
          onClick={(e) => { e.stopPropagation(); onToggleBookmark(policy.policy_id); }}
          disabled={bookmarkDisabled || policy.policy_id == null}
          className="bg-transparent border-none p-0.5 shrink-0"
          style={{ cursor: bookmarkDisabled || policy.policy_id == null ? 'default' : 'pointer' }}
        >
          <Bookmark size={18} color={isBookmarked ? '#3b82f6' : '#ccc'} fill={isBookmarked ? '#3b82f6' : 'none'} />
        </button>
      </div>

      {(badge || policy.apply_period) && (
        <div className="mt-2 flex items-center gap-1.5">
          {badge && (
            <span style={{
              padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 700,
              backgroundColor: badge.bg, color: badge.color,
            }}>
              {badge.label}
            </span>
          )}
          {policy.apply_period && <span className="text-[11px] text-gray-400">{policy.apply_period}</span>}
        </div>
      )}

      {policy.target && (
        <div className="mt-2">
          <p className="text-[11px] font-semibold text-gray-400">지원대상</p>
          <p className="mt-0.5 text-[12px] text-gray-600 leading-relaxed">{policy.target}</p>
        </div>
      )}

      {policy.policy_summary && (
        <div className="mt-2">
          <p className="text-[11px] font-semibold text-gray-400">지원내용 요약</p>
          <p className="mt-0.5 text-[12px] text-gray-600 leading-relaxed">{policy.policy_summary}</p>
        </div>
      )}

      {policy.required_fields?.length > 0 && (
        <button
          onClick={(e) => { e.stopPropagation(); onCheckIncome?.(policy); }}
          className="mt-3 cursor-pointer"
          style={{
            width: '100%', padding: '9px 0', borderRadius: 10,
            border: '1.5px solid #3b82f6', backgroundColor: '#fff',
            color: '#3b82f6', fontSize: 12.5, fontWeight: 700,
          }}
        >
          소득계산
        </button>
      )}

      {children}
    </div>
  );
}
