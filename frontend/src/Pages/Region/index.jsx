import { useRef, useState } from 'react';
import { ChevronLeft, ChevronUp, MapPin, ChevronDown, ChevronRight, ExternalLink, Bookmark } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useRegion from '../../hooks/useRegion';
import useBookmarks from '../../hooks/useBookmarks';

// 지역 프로그램 지도 검색 화면: 카카오맵 위에 검색 결과를 마커로 표시한다.
export default function RegionPage() {
  const {
    keyword,
    setKeyword,
    radius,
    setRadius,
    myLocation,
    loading,
    error,
    mapRef,
    handleGetLocation,
    handleSearch,
    statusFilter,
    toggleStatusFilter,
    expandedPlaces,
    togglePlace,
    filteredResults,
    groupedByPlace,
  } = useRegion();
  const { isLocalProgramBookmarked, toggleLocalProgramBookmark } = useBookmarks();
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const [showScrollTop, setShowScrollTop] = useState(false);

  const allStatuses = Object.keys(statusFilter);

  const handleScroll = (e) => {
    setShowScrollTop(e.target.scrollTop > 200);
  };

  const scrollToTop = () => {
    scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div style={{ backgroundColor: '#f5f6fa', height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <div className="flex items-center gap-2 bg-white" style={{ padding: '20px 20px 16px' }}>
        <button onClick={() => navigate(-1)} className="bg-transparent border-none cursor-pointer p-0 flex items-center">
          <ChevronLeft size={24} color="#333" />
        </button>
        <p className="text-[20px] font-extrabold text-gray-900">근처 프로그램 찾기</p>
      </div>

      <div ref={scrollRef} onScroll={handleScroll} style={{ flex: 1, overflowY: 'auto' }}>
      <div className="bg-white" style={{ padding: '0 20px 16px', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="배우고 싶은 것을 검색하세요 (예: 테니스)"
          style={{
            flex: 1,
            minWidth: 160,
            padding: '11px 14px',
            borderRadius: 999,
            border: '1px solid #e5e7eb',
            fontSize: 13,
            fontWeight: 500,
            color: '#374151',
            backgroundColor: '#f9fafb',
            boxSizing: 'border-box',
          }}
        />
        <button
          onClick={handleGetLocation}
          className="flex items-center gap-1 border-none cursor-pointer"
          style={{
            padding: '0 14px',
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 600,
            backgroundColor: myLocation ? '#3b82f6' : '#f3f4f6',
            color: myLocation ? '#fff' : '#4b5563',
          }}
        >
          <MapPin size={14} />
          내 위치
        </button>
        <select
          value={radius}
          onChange={(e) => setRadius(Number(e.target.value))}
          style={{
            padding: '0 10px',
            borderRadius: 999,
            border: '1px solid #e5e7eb',
            fontSize: 13,
            fontWeight: 600,
            color: '#374151',
            backgroundColor: '#f9fafb',
          }}
        >
          <option value={1}>1km</option>
          <option value={3}>3km</option>
          <option value={5}>5km</option>
          <option value={10}>10km</option>
        </select>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="border-none cursor-pointer"
          style={{
            padding: '0 18px',
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 700,
            backgroundColor: '#3b82f6',
            color: '#fff',
          }}
        >
          {loading ? '검색 중...' : '검색'}
        </button>
      </div>

      {error && (
        <div className="bg-white" style={{ padding: '0 20px 12px' }}>
          <p style={{ fontSize: 12, color: '#dc2626', margin: 0 }}>{error}</p>
        </div>
      )}

      <div className="bg-white border-b border-gray-100" style={{ padding: '0 20px 16px' }}>
        <div ref={mapRef} style={{ width: '100%', height: 260, borderRadius: 16, overflow: 'hidden', border: '1px solid #eee' }} />
      </div>

      {allStatuses.length > 0 && (
        <div className="bg-white overflow-x-auto no-scrollbar" style={{ display: 'flex', gap: 8, padding: '12px 20px', WebkitOverflowScrolling: 'touch' }}>
          {allStatuses.map((status) => (
            <button
              key={status}
              onClick={() => toggleStatusFilter(status)}
              style={{
                padding: '6px 14px',
                borderRadius: 999,
                fontSize: 12,
                fontWeight: 600,
                whiteSpace: 'nowrap',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: statusFilter[status] ? '#3b82f6' : '#f3f4f6',
                color: statusFilter[status] ? '#fff' : '#4b5563',
              }}
            >
              {status}
            </button>
          ))}
        </div>
      )}

      <div style={{ padding: '14px 20px 6px' }}>
        <p className="text-[12px] text-gray-400">
          검색 결과 {filteredResults.length}건 · {Object.keys(groupedByPlace).length}개 장소
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '4px 20px 24px' }}>
        {Object.keys(groupedByPlace).length === 0 ? (
          <div className="text-center py-10 text-[13px] text-gray-400">
            {keyword ? '검색 결과가 없습니다.' : '검색어를 입력하고 검색해보세요.'}
          </div>
        ) : (
          Object.entries(groupedByPlace).map(([placeName, items]) => {
            const isExpanded = expandedPlaces[placeName];
            return (
              <div key={placeName} style={{ backgroundColor: '#fff', borderRadius: 18, boxShadow: '0 2px 10px rgba(0,0,0,0.06)', overflow: 'hidden' }}>
                <button
                  onClick={() => togglePlace(placeName)}
                  className="w-full border-none cursor-pointer flex items-center justify-between bg-transparent"
                  style={{ padding: '14px 16px', textAlign: 'left' }}
                >
                  <span className="text-[14px] font-bold text-gray-900">{placeName} ({items.length}건)</span>
                  {isExpanded ? <ChevronDown size={16} color="#9ca3af" /> : <ChevronRight size={16} color="#9ca3af" />}
                </button>

                {isExpanded && (
                  <div style={{ padding: '0 16px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {items.map((item, idx) => (
                      <div key={idx} style={{ borderTop: '1px solid #f3f4f6', paddingTop: 10 }}>
                        <div className="flex items-center justify-between">
                          <p className="text-[13px] font-semibold text-gray-800" style={{ margin: 0 }}>{item.svcnm}</p>
                          <button
                            onClick={() => toggleLocalProgramBookmark(item.id)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', flexShrink: 0 }}
                          >
                            <Bookmark
                              size={16}
                              color={isLocalProgramBookmarked(item.id) ? '#3b82f6' : '#9ca3af'}
                              fill={isLocalProgramBookmarked(item.id) ? '#3b82f6' : 'none'}
                            />
                          </button>
                        </div>
                        <p className="text-[12px] text-gray-400" style={{ margin: '4px 0 0' }}>
                          {item.svcstatnm}
                          {item.distanceKm !== null && item.distanceKm !== undefined && ` · ${item.distanceKm}km`}
                        </p>
                        {item.applyUrl && (
                          <a
                            href={item.applyUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1"
                            style={{ marginTop: 6, fontSize: 12, fontWeight: 600, color: '#3b82f6', textDecoration: 'none' }}
                          >
                            신청하러 가기 <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
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
