export default function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center" style={{ padding: 28 }}>
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div
        className="relative bg-white rounded-2xl"
        style={{ width: '100%', maxWidth: 290, maxHeight: '70%', display: 'flex', flexDirection: 'column', boxShadow: '0 10px 40px rgba(0,0,0,0.25)' }}
      >
        <div style={{ padding: '20px 20px 4px', overflowY: 'auto' }}>
          {title && <h2 className="text-[15px] font-bold text-gray-900 mb-3 text-center">{title}</h2>}
          {children}
        </div>
        <button
          onClick={onClose}
          className="cursor-pointer"
          style={{
            width: '100%', padding: '13px 0', marginTop: 12,
            border: 'none', borderTop: '1px solid #f0f1f4', backgroundColor: 'transparent',
            color: '#3b82f6', fontSize: 14, fontWeight: 700,
          }}
        >
          확인
        </button>
      </div>
    </div>
  );
}
