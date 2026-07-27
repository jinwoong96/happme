import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronUp, Search, Plus, X } from 'lucide-react';
import useNotification from '../../hooks/useNotification';

// 알림 설정 화면: 즐겨찾기별 마감 알림 on/off, 검색, 공고문 키워드 알림 등록/삭제.
export default function NotificationPage() {
  const {
    filtered, search, setSearch, toggle, loading, isEmpty,
    keywords, keywordError, addKeyword, removeKeyword,
  } = useNotification();
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showKeywordInput, setShowKeywordInput] = useState(false);
  const [keywordInput, setKeywordInput] = useState('');

  const handleScroll = (e) => {
    setShowScrollTop(e.target.scrollTop > 200);
  };

  const scrollToTop = () => {
    scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmitKeyword = async () => {
    const ok = await addKeyword(keywordInput);
    if (ok) {
      setKeywordInput('');
      setShowKeywordInput(false);
    }
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[20px] font-bold text-gray-900">정책알림</p>
      </div>

      <div className="bg-white border-b border-gray-100" style={{ padding: '12px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, backgroundColor: '#f5f6fa', borderRadius: 14, padding: '11px 14px' }}>
          <Search size={16} color="#aaa" />
          <input
            value={search} onChange={(e) => setSearch(e.target.value)} placeholder="정책 검색..."
            style={{
              flex: 1, border: 'none', backgroundColor: 'transparent',
              fontSize: 14, color: '#1f2937', outline: 'none',
              appearance: 'none', WebkitAppearance: 'none',
            }}
          />
        </div>
      </div>

      <div ref={scrollRef} onScroll={handleScroll} style={{ flex: 1, overflowY: 'auto', backgroundColor: '#fff' }}>
        {loading
          ? <div className="text-center py-10 text-[13px] text-gray-400">불러오는 중...</div>
          : isEmpty
          ? <div className="text-center py-10 text-[13px] text-gray-400">즐겨찾기한 정책이 없어요. 전체보기에서 관심있는 정책을 즐겨찾기 해보세요.</div>
          : filtered.length === 0
          ? <div className="text-center py-10 text-[13px] text-gray-400">검색 결과가 없습니다.</div>
          : filtered.map((item, i) => (
            <div key={item.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 20px',
              borderBottom: i < filtered.length - 1 ? '1px solid #f9fafb' : 'none',
            }}>
              <div style={{ flex: 1, marginRight: 12 }}>
                <p className="text-[14px] font-semibold text-gray-900">{item.title}</p>
                <p className="mt-0.5 text-[12px] text-gray-400">{item.org ? `${item.org} · ` : ''}마감 {item.deadline}</p>
              </div>
              <button onClick={() => toggle(item.id)}
                style={{
                  width: 46, height: 26, borderRadius: 999, border: 'none', cursor: 'pointer',
                  backgroundColor: item.on ? '#3b82f6' : '#e5e7eb',
                  position: 'relative', flexShrink: 0, transition: 'background-color 0.2s',
                }}>
                <div style={{
                  position: 'absolute', top: 3,
                  left: item.on ? 23 : 3,
                  width: 20, height: 20, borderRadius: '50%', backgroundColor: '#fff',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
                  transition: 'left 0.2s',
                }} />
              </button>
            </div>
          ))
        }
      </div>

      <div style={{ backgroundColor: '#fff', borderTop: '1px solid #f3f4f6', padding: '14px 20px', flexShrink: 0 }}>
        {keywords.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
            {keywords.map((k) => (
              <div key={k.keyword_id} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                backgroundColor: '#eff6ff', color: '#3b82f6', borderRadius: 999,
                padding: '6px 6px 6px 12px', fontSize: 13, fontWeight: 500,
              }}>
                <span>{k.keyword}</span>
                <button
                  onClick={() => removeKeyword(k.keyword_id)}
                  style={{
                    border: 'none', background: 'transparent', cursor: 'pointer',
                    color: '#93c5fd', display: 'flex', padding: 4,
                  }}
                >
                  <X size={13} />
                </button>
              </div>
            ))}
          </div>
        )}

        {showKeywordInput ? (
          <div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmitKeyword()}
                placeholder="예: 전세보증금, 대학생 월세 등 관심 있는 내용을 입력해주세요"
                autoFocus
                style={{
                  flex: 1, border: '1px solid #e5e7eb', borderRadius: 12, padding: '11px 14px',
                  fontSize: 14, color: '#1f2937', outline: 'none',
                }}
              />
              <button
                onClick={handleSubmitKeyword}
                disabled={!keywordInput.trim()}
                style={{
                  border: 'none', borderRadius: 12, padding: '0 18px',
                  backgroundColor: keywordInput.trim() ? '#3b82f6' : '#e5e7eb',
                  color: '#fff', fontSize: 14, fontWeight: 600,
                  cursor: keywordInput.trim() ? 'pointer' : 'default',
                }}
              >
                등록
              </button>
            </div>
            {keywordError && <p style={{ marginTop: 6, fontSize: 12, color: '#ef4444' }}>{keywordError}</p>}
          </div>
        ) : (
          <button
            onClick={() => setShowKeywordInput(true)}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              border: '1px dashed #93c5fd', borderRadius: 14, padding: '13px 0',
              backgroundColor: '#f5f7ff', color: '#3b82f6', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}
          >
            <Plus size={16} /> 관심 공고 알림 받기
          </button>
        )}
      </div>

      {showScrollTop && (
        <button
          onClick={scrollToTop}
          style={{
            position: 'absolute', right: 20, bottom: 20, width: 44, height: 44,
            borderRadius: '50%', border: 'none', backgroundColor: '#3b82f6', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(59,130,246,0.4)',
          }}
        >
          <ChevronUp size={22} />
        </button>
      )}
    </div>
  );
}
