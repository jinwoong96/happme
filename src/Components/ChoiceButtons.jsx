const buttonStyle = (active) => ({
  width: '100%',
  padding: '13px 0',
  borderRadius: 14,
  fontSize: 14,
  fontWeight: 700,
  cursor: 'pointer',
  border: active ? '1.5px solid #3b82f6' : '1.5px solid #e5e7eb',
  backgroundColor: active ? '#eff6ff' : '#fff',
  color: active ? '#3b82f6' : '#6b7280',
});

// 프로필 입력 폼에서 쓰는 단순 버튼형 선택지 (성별, 예/아니오 등)
export function ToggleGroup({ options, value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 10 }}>
      {options.map((opt) => (
        <button
          key={String(opt.value)}
          type="button"
          onClick={() => onChange(opt.value)}
          style={{ flex: 1, ...buttonStyle(value === opt.value) }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// 옵션 중 하나(hasInput: true)를 선택하면 버튼 자리가 바로 텍스트 입력으로 바뀌는 선택지.
// 시나리오 Q1(지역 쓰기)/Q2(기타)처럼 "선택 + 직접 입력"이 함께 필요한 경우에 쓴다.
export function ChoiceButtonsWithInput({ options, value, onChange, textValue, onTextChange, textPlaceholder }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
      {options.map((opt) => {
        const active = value === opt.value;
        const showInput = opt.hasInput && active;

        return (
          <div key={opt.value} style={{ flex: showInput ? '1 1 100%' : '1 1 0', minWidth: showInput ? '100%' : 0 }}>
            {showInput ? (
              <input
                autoFocus
                value={textValue ?? ''}
                onChange={(e) => onTextChange(e.target.value)}
                placeholder={textPlaceholder}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  outline: 'none',
                  fontFamily: 'inherit',
                  ...buttonStyle(true),
                  textAlign: 'left',
                  padding: '13px 16px',
                }}
              />
            ) : (
              <button type="button" onClick={() => onChange(opt.value)} style={buttonStyle(active)}>
                {opt.label}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
