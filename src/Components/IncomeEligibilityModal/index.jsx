import { useState } from 'react';
import { api } from '../../utils/api';
import { INCOME_QUESTIONS, UNKNOWN_ANSWER } from '../../data/incomeQuestions';

// 정책 카드의 "소득계산" 버튼에서 뜨는 모달. requiredFields에 해당하는 질문만 물어보고,
// 답변을 그 자리에서 판정에만 쓰고 저장하지는 않는다.
export default function IncomeEligibilityModal({ plcyNo, requiredFields, onClose }) {
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  if (!plcyNo || !requiredFields?.length) return null;

  // requiredFields가 어떤 순서로 오든, INCOME_QUESTIONS에 정의된 고정 순서대로만 질문한다.
  // (해당 없는 질문은 자동으로 빠짐)
  const orderedFields = Object.keys(INCOME_QUESTIONS).filter((key) => requiredFields.includes(key));

  const setAnswer = (key, value) => setAnswers((prev) => ({ ...prev, [key]: value }));

  // dependsOn이 걸린 질문(예: annual_sales는 is_business_owner가 true일 때만 의미 있음)은
  // 조건이 안 맞으면 "해당없음"으로 자동 처리되므로 답변을 채우지 않아도 다음으로 넘어갈 수 있다.
  const isNotApplicable = (key) => {
    const dependsOn = INCOME_QUESTIONS[key]?.dependsOn;
    return dependsOn ? answers[dependsOn.key] !== dependsOn.value : false;
  };
  const isFilled = orderedFields.every(
    (key) => isNotApplicable(key) || (answers[key] !== undefined && answers[key] !== '')
  );

  // 입력값은 콤마 없는 순수 숫자 문자열로 저장(백엔드로 그대로 전송)하고, 화면 표시만 콤마를 붙인다.
  const formatWithCommas = (value) => {
    if (value === undefined || value === null || value === '') return '';
    const digits = String(value).replace(/[^\d]/g, '');
    if (!digits) return '';
    return Number(digits).toLocaleString('ko-KR');
  };
  const handleNumberChange = (key, raw) => setAnswer(key, raw.replace(/[^\d]/g, ''));

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      const data = await api.post('/recommendations/income-eligibility', { plcyNo, answers });
      setResult(data);
    } catch (err) {
      setError(err.message || '판정 중 오류가 발생했어요.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center" style={{ padding: 28 }}>
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div
        className="relative bg-white rounded-2xl"
        style={{ width: '100%', maxWidth: 300, maxHeight: '78%', display: 'flex', flexDirection: 'column', boxShadow: '0 10px 40px rgba(0,0,0,0.25)' }}
      >
        <div style={{ padding: '20px 20px 4px', overflowY: 'auto' }}>
          <h2 className="text-[15px] font-bold text-gray-900 mb-3 text-center">
            {result ? '소득 조건 확인 결과' : '소득 조건 확인'}
          </h2>

          {!result ? (
            <div className="flex flex-col gap-3">
              {orderedFields.map((key) => {
                const q = INCOME_QUESTIONS[key];
                if (!q) return null;
                const isUnknown = answers[key] === UNKNOWN_ANSWER;
                const notApplicable = isNotApplicable(key);
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1.5">
                      <p className="text-[12.5px] font-semibold text-gray-700">{q.label}</p>
                      {!notApplicable && q.allowUnknown && (
                        <button
                          type="button"
                          onClick={() => setAnswer(key, isUnknown ? '' : UNKNOWN_ANSWER)}
                          className="cursor-pointer"
                          style={{
                            border: 'none', background: 'transparent', padding: 0,
                            fontSize: 11.5, fontWeight: 600,
                            color: isUnknown ? '#ef4444' : '#f87171',
                            textDecoration: isUnknown ? 'underline' : 'none',
                          }}
                        >
                          모르겠어요
                        </button>
                      )}
                    </div>
                    {notApplicable ? (
                      <div
                        style={{
                          padding: '9px 12px', borderRadius: 10, fontSize: 13,
                          border: '1.5px solid #e5e7eb', backgroundColor: '#f9fafb', color: '#9ca3af',
                        }}
                      >
                        해당없음
                      </div>
                    ) : q.type === 'boolean' ? (
                      <div className="flex gap-2">
                        {[{ label: '예', value: true }, { label: '아니오', value: false }].map((opt) => (
                          <button
                            key={opt.label}
                            onClick={() => setAnswer(key, opt.value)}
                            style={{
                              flex: 1, padding: '9px 0', borderRadius: 10, fontSize: 13, fontWeight: 600,
                              border: `1.5px solid ${answers[key] === opt.value ? '#3b82f6' : '#e5e7eb'}`,
                              backgroundColor: answers[key] === opt.value ? '#eff6ff' : '#fff',
                              color: answers[key] === opt.value ? '#3b82f6' : '#6b7280',
                              cursor: 'pointer',
                            }}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    ) : isUnknown ? (
                      <div
                        style={{
                          padding: '9px 12px', borderRadius: 10, fontSize: 13,
                          border: '1.5px solid #fecaca', backgroundColor: '#fef2f2', color: '#ef4444',
                        }}
                      >
                        모르겠어요로 답변했어요
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="text"
                          inputMode="numeric"
                          value={formatWithCommas(answers[key])}
                          onChange={(e) => handleNumberChange(key, e.target.value)}
                          placeholder="숫자만 입력"
                          style={{
                            flex: 1, padding: '9px 12px', borderRadius: 10, fontSize: 13,
                            border: '1.5px solid #e5e7eb', outline: 'none', boxSizing: 'border-box',
                          }}
                        />
                        {q.unit && <span className="text-[12px] text-gray-400">{q.unit}</span>}
                      </div>
                    )}
                  </div>
                );
              })}
              {error && <p className="text-[12px] text-red-500">{error}</p>}
            </div>
          ) : (
            <div className="flex flex-col items-center" style={{ padding: '8px 0 16px' }}>
              <span
                style={{
                  padding: '5px 14px', borderRadius: 999, fontSize: 13, fontWeight: 700, marginBottom: 10,
                  backgroundColor: result.eligible === null ? '#f3f4f6' : result.eligible ? '#dcfce7' : '#fee2e2',
                  color: result.eligible === null ? '#6b7280' : result.eligible ? '#16a34a' : '#ef4444',
                }}
              >
                {result.eligible === null ? '확인 필요' : result.eligible ? '지원 가능' : '지원 불가'}
              </span>
              <p className="text-[12.5px] text-gray-600 leading-relaxed text-center">{result.reason}</p>
            </div>
          )}
        </div>

        <button
          onClick={result ? onClose : handleSubmit}
          disabled={!result && (!isFilled || submitting)}
          className="cursor-pointer"
          style={{
            width: '100%', padding: '13px 0', marginTop: 12,
            border: 'none', borderTop: '1px solid #f0f1f4', backgroundColor: 'transparent',
            color: !result && (!isFilled || submitting) ? '#c3c9d4' : '#3b82f6',
            fontSize: 14, fontWeight: 700,
            cursor: !result && (!isFilled || submitting) ? 'default' : 'pointer',
          }}
        >
          {result ? '닫기' : submitting ? '판정 중...' : '확인하기'}
        </button>
      </div>
    </div>
  );
}
