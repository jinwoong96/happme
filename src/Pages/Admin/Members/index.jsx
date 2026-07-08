import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Trash2 } from 'lucide-react';
import useAdminMembers from '../../../hooks/useAdminMembers';
import Modal from '../../../Components/Modal';

export default function AdminMembersPage() {
  const navigate = useNavigate();
  const { members, loading, error, deleteMember } = useAdminMembers();
  const [target, setTarget] = useState(null); // 삭제할 회원
  const [deleteError, setDeleteError] = useState('');

  const handleConfirmDelete = async () => {
    setDeleteError('');
    try {
      await deleteMember(target.user_id);
      setTarget(null);
    } catch (err) {
      setDeleteError(err.message);
    }
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', minHeight: '100%' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate('/admin')} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[18px] font-bold text-gray-900">회원 관리</p>
      </div>

      <div style={{ padding: '16px 20px 24px' }}>
        <p className="text-[13px] text-gray-400" style={{ marginBottom: 12 }}>전체 회원 {members.length}명</p>

        {loading ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#9ca3af' }}>불러오는 중...</div>
        ) : error ? (
          <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, textAlign: 'center', fontSize: 13, color: '#ef4444' }}>{error}</div>
        ) : (
          <div className="flex flex-col gap-2.5">
            {members.map((m) => (
              <div key={m.user_id} style={{ display: 'flex', alignItems: 'center', gap: 12, backgroundColor: '#fff', borderRadius: 18, padding: '14px 16px', boxShadow: '0 2px 10px rgba(0,0,0,0.06)' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="flex items-center gap-2">
                    <p className="text-[14px] font-bold text-gray-900" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.name || '(이름 없음)'}</p>
                    {m.role === 'ADMIN' && (
                      <span style={{ padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 700, backgroundColor: '#eff6ff', color: '#3b82f6', flexShrink: 0 }}>ADMIN</span>
                    )}
                  </div>
                  <p className="mt-0.5 text-[12px] text-gray-400" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.email}</p>
                </div>
                <button
                  onClick={() => setTarget(m)}
                  disabled={m.role === 'ADMIN'}
                  title={m.role === 'ADMIN' ? '관리자 계정은 삭제할 수 없습니다' : '회원 삭제'}
                  style={{
                    border: 'none', background: 'none', padding: 6, flexShrink: 0,
                    cursor: m.role === 'ADMIN' ? 'not-allowed' : 'pointer',
                    opacity: m.role === 'ADMIN' ? 0.3 : 1,
                  }}
                >
                  <Trash2 size={18} color="#ef4444" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal isOpen={!!target} onClose={() => setTarget(null)} title="회원을 삭제할까요?">
        <div className="flex flex-col gap-3" style={{ paddingBottom: 8 }}>
          <p className="text-[13px] text-gray-500 text-center">
            {target?.name} ({target?.email}) 회원을 삭제합니다.<br />이 작업은 되돌릴 수 없습니다.
          </p>
          {deleteError && <p className="text-[12px] text-red-400 text-center">{deleteError}</p>}
          <button
            onClick={handleConfirmDelete}
            style={{ width: '100%', padding: '13px 0', borderRadius: 14, border: 'none', backgroundColor: '#ef4444', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
          >
            삭제하기
          </button>
        </div>
      </Modal>
    </div>
  );
}
