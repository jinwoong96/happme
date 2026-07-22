import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Bell, Trash2 } from 'lucide-react';
import useAlerts from '../../hooks/useAlerts';
import usePolicyDetail from '../../hooks/usePolicyDetail';
import useBookmarks from '../../hooks/useBookmarks';
import PolicyDetailModal from '../../Components/PolicyDetailModal';
import Modal from '../../Components/Modal';

const TYPE_LABEL = {
  NOTICE: { label: '공지', bg: '#eff6ff', color: '#3b82f6' },
  INQUIRY_ANSWER: { label: '문의 답변', bg: '#f0fdf4', color: '#22c55e' },
  SYSTEM: { label: '시스템', bg: '#f5f6fa', color: '#6b7280' },
  NEW_POLICY: { label: '새 정책', bg: '#fdf2f8', color: '#ec4899' },
  BOOKMARK: { label: '즐겨찾기', bg: '#fffbeb', color: '#f59e0b' },
  KEYWORD_MATCH: { label: '관심 공고', bg: '#eef2ff', color: '#6366f1' },
};

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

// "[전세보증금] 지원 가능한 공고문이 있어요" -> { tag: "[전세보증금]", rest: "지원 가능한 공고문이 있어요" }
// 대괄호 태그로 시작하지 않는 제목(다른 알림 타입)은 그대로 rest에만 담아 기존과 동일하게 보인다.
function parseAlertTitle(title) {
  const match = /^(\[[^\]]+\])\s*(.*)$/.exec(title || '');
  return match ? { tag: match[1], rest: match[2] } : { tag: null, rest: title };
}

export default function AlertsPage() {
  const navigate = useNavigate();
  const { alerts, loading, markRead, markAllRead, removeAlert } = useAlerts();
  const { selectedPolicy, policyLoading, openPolicy, closePolicy } = usePolicyDetail();
  const { isBookmarked, toggleBookmark, loading: bookmarksLoading } = useBookmarks();
  const unreadCount = alerts.filter((a) => !a.is_read).length;
  // policy_id가 없는(연결된 공고문 정보가 유실된) 알림은 상세 모달을 열 수 없으니,
  // 알림 자체에 이미 있는 제목/내용만이라도 보여준다.
  const [plainAlert, setPlainAlert] = useState(null);

  const handleOpenAlert = (a) => {
    if (!a.is_read) markRead(a.notification_id);
    if (a.policy_id != null) {
      openPolicy(a.policy_id, a.title, isBookmarked(a.policy_id));
    } else {
      setPlainAlert(a);
    }
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="flex-1 text-[20px] font-bold text-gray-900">알림함</p>
        {unreadCount > 0 && (
          <button onClick={markAllRead} style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#3b82f6' }}>
            모두 읽음
          </button>
        )}
      </div>

      <div style={{ padding: '16px 20px 24px' }}>
        {loading ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>불러오는 중...</div>
        ) : alerts.length === 0 ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 36, textAlign: 'center' }}>
            <Bell size={32} color="#d1d5db" style={{ margin: '0 auto 10px' }} />
            <p className="text-[13px] text-gray-400">받은 알림이 없어요.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2.5">
            {alerts.map((a) => {
              const type = TYPE_LABEL[a.notify_type] || TYPE_LABEL.SYSTEM;
              const isKeywordMatch = a.notify_type === 'KEYWORD_MATCH';
              return (
                <div
                  key={a.notification_id}
                  onClick={() => handleOpenAlert(a)}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left', cursor: 'pointer',
                    backgroundColor: isKeywordMatch ? '#f5f6ff' : '#fff', borderRadius: 18, padding: '16px 44px 16px 18px',
                    boxShadow: isKeywordMatch ? '0 2px 10px rgba(99,102,241,0.15)' : '0 2px 10px rgba(0,0,0,0.06)',
                    border: isKeywordMatch ? '1px solid #e0e3ff' : '1px solid transparent',
                    borderLeft: isKeywordMatch ? '4px solid #6366f1' : '4px solid transparent',
                    position: 'relative',
                  }}
                >
                  {!a.is_read && <span style={{ position: 'absolute', top: 16, right: 44, width: 7, height: 7, borderRadius: '50%', backgroundColor: '#3b82f6' }} />}
                  <button
                    onClick={(e) => { e.stopPropagation(); removeAlert(a.notification_id); }}
                    style={{
                      position: 'absolute', top: 14, right: 14, padding: 4, border: 'none',
                      background: 'none', cursor: 'pointer', display: 'flex',
                    }}
                    aria-label="알림 삭제"
                  >
                    <Trash2 size={15} color="#d1d5db" />
                  </button>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold" style={{ padding: '2px 8px', borderRadius: 999, backgroundColor: type.bg, color: type.color }}>
                      {type.label}
                    </span>
                    <span className="text-[11px] text-gray-400">{formatDate(a.created_at)}</span>
                  </div>
                  {(() => {
                    const { tag, rest } = parseAlertTitle(a.title);
                    return tag ? (
                      <div className="mt-1.5">
                        <p className="text-[14px] font-bold text-gray-900">{tag}</p>
                        {rest && <p className="mt-0.5 text-[12.5px] text-gray-400">{rest}</p>}
                      </div>
                    ) : (
                      <p className="mt-1.5 text-[14px] font-bold text-gray-900">{a.title}</p>
                    );
                  })()}
                  {a.content && <p className="mt-1 text-[12px] text-gray-500">{a.content}</p>}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <PolicyDetailModal
        selectedPolicy={selectedPolicy}
        policyLoading={policyLoading}
        isBookmarked={isBookmarked(selectedPolicy?.policy_id, selectedPolicy?.is_bookmarked)}
        onToggleBookmark={toggleBookmark}
        bookmarkDisabled={bookmarksLoading}
        onClose={closePolicy}
      />

      <Modal isOpen={!!plainAlert} onClose={() => setPlainAlert(null)} maxWidth={320}>
        {plainAlert && (() => {
          const type = TYPE_LABEL[plainAlert.notify_type] || TYPE_LABEL.SYSTEM;
          const { tag, rest } = parseAlertTitle(plainAlert.title);
          return (
            <div>
              <div className="flex justify-center">
                <span className="text-[11px] font-bold" style={{ padding: '3px 10px', borderRadius: 999, backgroundColor: type.bg, color: type.color }}>
                  {type.label}
                </span>
              </div>
              {tag ? (
                <div className="mt-2.5 text-center">
                  <p className="text-[15px] font-bold text-gray-900">{tag}</p>
                  {rest && <p className="mt-0.5 text-[13px] text-gray-400">{rest}</p>}
                </div>
              ) : (
                <h2 className="mt-2.5 text-[15px] font-bold text-gray-900 text-center" style={{ lineHeight: 1.4 }}>
                  {plainAlert.title}
                </h2>
              )}
              <p className="mt-3 text-[13.5px] text-gray-700" style={{ lineHeight: 1.7 }}>{plainAlert.content}</p>
              <div className="mt-3" style={{ backgroundColor: '#f5f6fa', borderRadius: 10, padding: '10px 12px' }}>
                <p className="text-[11.5px] text-gray-400" style={{ lineHeight: 1.5 }}>
                  연결된 공고문 정보를 더 이상 확인할 수 없어요.
                </p>
              </div>
            </div>
          );
        })()}
      </Modal>
    </div>
  );
}
