import { useState } from 'react';
import { api } from '../../utils/api';
import { INCOME_QUESTIONS } from '../../data/incomeQuestions';

// 정책 카드의 "소득계산" 버튼에서 뜨는 모달. requiredFields에 해당하는 질문만 물어보고,
// 답변을 그 자리에서 판정에만 쓰고 저장하지는 않는다.
export default function IncomeEligibilityModal({ plcyNo, requiredFields, onClose }) {
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  if (!plcyNo || !requiredFields?.length) return null;

  const setAnswer = (key, value) => setAnswers((prev) => ({ ...prev, [key]: value }));
  const isFilled = requiredFields.every((key) => answers[key] !== undefined && answers[key] !== '');

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
              {requiredFields.map((key) => {
                const q = INCOME_QUESTIONS[key];
                if (!q) return null;
                return (
                  <div key={key}>
                    <p className="text-[12.5px] font-semibold text-gray-700 mb-1.5">{q.label}</p>
                    {q.type === 'boolean' ? (
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
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="number"
                          value={answers[key] ?? ''}
                          onChange={(e) => setAnswer(key, e.target.value)}
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
                  backgroundColor: result.eligible ? '#dcfce7' : '#fee2e2',
                  color: result.eligible ? '#16a34a' : '#ef4444',
                }}
              >
                {result.eligible ? '지원 가능' : '지원 불가'}
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
