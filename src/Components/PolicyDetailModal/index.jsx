import { Bookmark, ExternalLink } from 'lucide-react';
import Modal from '../Modal';

export default function PolicyDetailModal({ selectedPolicy, policyLoading, isBookmarked, onToggleBookmark, bookmarkDisabled, onClose }) {
  return (
    <Modal isOpen={!!selectedPolicy} onClose={onClose} title={selectedPolicy?.plcyNm}>
      {selectedPolicy && (
        <div className="flex flex-col gap-4">
          <button
            onClick={() => onToggleBookmark(selectedPolicy.policy_id)}
            disabled={bookmarkDisabled || selectedPolicy.policy_id == null}
            className="flex items-center gap-1.5 bg-transparent border-none p-0 self-start"
            style={{ cursor: bookmarkDisabled || selectedPolicy.policy_id == null ? 'default' : 'pointer' }}
          >
            <Bookmark
              size={18}
              color={isBookmarked ? '#3b82f6' : '#9ca3af'}
              fill={isBookmarked ? '#3b82f6' : 'none'}
            />
            <span className="text-[13px] font-semibold" style={{ color: isBookmarked ? '#3b82f6' : '#6b7280' }}>
              {isBookmarked ? '즐겨찾기 됨' : '즐겨찾기 추가'}
            </span>
          </button>

          {policyLoading ? (
            <p className="text-[13px] text-gray-400">불러오는 중...</p>
          ) : selectedPolicy.error ? (
            <p className="text-[13px] text-red-400">{selectedPolicy.error}</p>
          ) : (
            <>
              {selectedPolicy.plcyExplnCn && (
                <div>
                  <p className="text-[13px] font-bold text-gray-700 mb-1">정책 설명</p>
                  <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.plcyExplnCn}</p>
                </div>
              )}
              {selectedPolicy.plcySprtCn && (
                <div>
                  <p className="text-[13px] font-bold text-gray-700 mb-1">지원 내용</p>
                  <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.plcySprtCn}</p>
                </div>
              )}
              {(selectedPolicy.sprtTrgtMinAge != null || selectedPolicy.sprtTrgtMaxAge != null) && (
                <div>
                  <p className="text-[13px] font-bold text-gray-700 mb-1">지원 대상 연령</p>
                  <p className="text-[13px] text-gray-600">{selectedPolicy.sprtTrgtMinAge}세 ~ {selectedPolicy.sprtTrgtMaxAge}세</p>
                </div>
              )}
              {selectedPolicy.aplyYmd && (
                <div>
                  <p className="text-[13px] font-bold text-gray-700 mb-1">신청 기간</p>
                  <p className="text-[13px] text-gray-600">{selectedPolicy.aplyYmd}</p>
                </div>
              )}
              {selectedPolicy.plcyAplyMthdCn && (
                <div>
                  <p className="text-[13px] font-bold text-gray-700 mb-1">신청 방법</p>
                  <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.plcyAplyMthdCn}</p>
                </div>
              )}
              {selectedPolicy.sbmsnDcmntCn && (
                <div>
                  <p className="text-[13px] font-bold text-gray-700 mb-1">제출 서류</p>
                  <p className="text-[13px] text-gray-600 leading-relaxed">{selectedPolicy.sbmsnDcmntCn}</p>
                </div>
              )}
              {selectedPolicy.aplyUrlAddr && (
                <a
                  href={selectedPolicy.aplyUrlAddr}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5"
                  style={{ color: '#3b82f6', fontSize: 13, fontWeight: 700, textDecoration: 'none' }}
                >
                  신청 바로가기 <ExternalLink size={14} />
                </a>
              )}
            </>
          )}
        </div>
      )}
    </Modal>
  );
}
