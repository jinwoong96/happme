export default function PhoneFrame({ children }) {
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* 폰 외곽 */}
      <div
        style={{
          width: 390,
          height: 844,
          background: '#1a1a1a',
          borderRadius: 52,
          padding: 10,
          boxShadow: '0 0 0 2px #3a3a3a, inset 0 0 0 1px #555',
          position: 'relative',
          flexShrink: 0,
        }}
      >
        {/* 사이드 버튼 - 볼륨 */}
        <div style={{ position: 'absolute', left: -3, top: 140, width: 3, height: 34, background: '#3a3a3a', borderRadius: '2px 0 0 2px' }} />
        <div style={{ position: 'absolute', left: -3, top: 184, width: 3, height: 34, background: '#3a3a3a', borderRadius: '2px 0 0 2px' }} />
        {/* 사이드 버튼 - 전원 */}
        <div style={{ position: 'absolute', right: -3, top: 180, width: 3, height: 64, background: '#3a3a3a', borderRadius: '0 2px 2px 0' }} />

        {/* 내부 스크린 */}
        <div
          style={{
            width: '100%',
            height: '100%',
            background: '#f9fafb',
            borderRadius: 44,
            overflow: 'hidden',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* 다이나믹 아일랜드 */}
          <div
            style={{
              position: 'absolute',
              top: 12,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 120,
              height: 34,
              background: '#1a1a1a',
              borderRadius: 20,
              zIndex: 100,
              pointerEvents: 'none',
            }}
          />

          {/* 상태바 */}
          <div
            style={{
              flexShrink: 0,
              height: 54,
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-between',
              padding: '0 28px 6px',
              zIndex: 99,
              fontSize: 13,
              fontWeight: 600,
              color: '#111',
            }}
          >
            <span>9:41</span>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <svg width="17" height="12" viewBox="0 0 17 12" fill="none">
                <rect x="0" y="3" width="3" height="9" rx="1" fill="#111" />
                <rect x="4.5" y="2" width="3" height="10" rx="1" fill="#111" />
                <rect x="9" y="1" width="3" height="11" rx="1" fill="#111" />
                <rect x="13.5" y="0" width="3" height="12" rx="1" fill="#111" />
              </svg>
              <svg width="16" height="12" viewBox="0 0 16 12" fill="none">
                <path d="M8 2.5C10.2 2.5 12.2 3.4 13.6 4.9L15 3.4C13.2 1.5 10.7 0.3 8 0.3C5.3 0.3 2.8 1.5 1 3.4L2.4 4.9C3.8 3.4 5.8 2.5 8 2.5Z" fill="#111"/>
                <path d="M8 5.5C9.5 5.5 10.9 6.1 11.9 7.1L13.3 5.6C11.9 4.2 10 3.3 8 3.3C6 3.3 4.1 4.2 2.7 5.6L4.1 7.1C5.1 6.1 6.5 5.5 8 5.5Z" fill="#111"/>
                <circle cx="8" cy="10" r="2" fill="#111"/>
              </svg>
              <div style={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <div style={{ width: 22, height: 11, border: '1.5px solid #111', borderRadius: 3, padding: 1.5, display: 'flex', alignItems: 'center' }}>
                  <div style={{ width: '75%', height: '100%', background: '#111', borderRadius: 1 }} />
                </div>
              </div>
            </div>
          </div>

          {/* 앱 콘텐츠 영역 — 스크롤 가능 */}
          <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
