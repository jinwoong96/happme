import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Bell } from 'lucide-react';
import useAlerts from '../../hooks/useAlerts';

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

export default function AlertsPage() {
  const navigate = useNavigate();
  const { alerts, loading, markRead, markAllRead } = useAlerts();
  const unreadCount = alerts.filter((a) => !a.is_read).length;

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
              return (
                <button
                  key={a.notification_id}
                  onClick={() => !a.is_read && markRead(a.notification_id)}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left', border: 'none', cursor: a.is_read ? 'default' : 'pointer',
                    backgroundColor: '#fff', borderRadius: 18, padding: '16px 18px',
                    boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
                    position: 'relative',
                  }}
                >
                  {!a.is_read && <span style={{ position: 'absolute', top: 16, right: 16, width: 7, height: 7, borderRadius: '50%', backgroundColor: '#3b82f6' }} />}
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold" style={{ padding: '2px 8px', borderRadius: 999, backgroundColor: type.bg, color: type.color }}>
                      {type.label}
                    </span>
                    <span className="text-[11px] text-gray-400">{formatDate(a.created_at)}</span>
                  </div>
                  <p className="mt-1.5 text-[14px] font-bold text-gray-900">{a.title}</p>
                  {a.content && <p className="mt-1 text-[12px] text-gray-500">{a.content}</p>}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
