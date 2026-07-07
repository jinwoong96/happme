import { useState, useEffect, useRef, useMemo } from 'react';
import { api } from '../utils/api';

export default function useRegion() {
  const [keyword, setKeyword] = useState('');
  const [radius, setRadius] = useState(3);
  const [myLocation, setMyLocation] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState({});
  const [expandedPlaces, setExpandedPlaces] = useState({});

  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);
  const myLocationOverlayRef = useRef(null);

  useEffect(() => {
    if (!window.kakao) {
      setError('카카오맵 SDK를 불러오지 못했어요.');
      return;
    }
    window.kakao.maps.load(() => {
      const container = mapRef.current;
      if (!container) return;
      const options = {
        center: new window.kakao.maps.LatLng(37.5735, 126.9788),
        level: 6,
      };
      mapInstance.current = new window.kakao.maps.Map(container, options);
    });
  }, []);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setError('이 브라우저는 위치 기능을 지원하지 않아요.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        setMyLocation({ lat, lng });
        setError('');

        if (mapInstance.current) {
          const moveLatLng = new window.kakao.maps.LatLng(lat, lng);
          mapInstance.current.setCenter(moveLatLng);

          if (myLocationOverlayRef.current) {
            myLocationOverlayRef.current.setMap(null);
          }

          const content = `
            <div style="
              width: 16px; height: 16px;
              background: #3b82f6;
              border: 3px solid white;
              border-radius: 50%;
              box-shadow: 0 0 4px rgba(0,0,0,0.4);
            "></div>
          `;
          const overlay = new window.kakao.maps.CustomOverlay({
            position: moveLatLng,
            content,
            map: mapInstance.current,
            yAnchor: 0.5,
          });
          myLocationOverlayRef.current = overlay;
        }
      },
      (err) => {
        setError('위치 권한을 허용해주세요. (' + err.message + ')');
      }
    );
  };

  const clearMarkers = () => {
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];
  };

  const handleSearch = async () => {
    if (!keyword.trim()) return;
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams({ keyword });
      if (myLocation) {
        params.append('lat', myLocation.lat);
        params.append('lng', myLocation.lng);
        params.append('radius', radius);
      }

      const data = await api.get(`/local-programs/search?${params.toString()}`);
      const items = data.results || [];
      setResults(items);

      const uniqueStatuses = [...new Set(items.map((r) => r.svcstatnm))];
      const initialFilter = {};
      uniqueStatuses.forEach((s) => (initialFilter[s] = true));
      setStatusFilter(initialFilter);
      setExpandedPlaces({});

      clearMarkers();
      if (mapInstance.current && items.length > 0) {
        const bounds = new window.kakao.maps.LatLngBounds();

        const redMarkerSvg = `
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="42" viewBox="0 0 32 42">
            <path d="M16 0C7.163 0 0 7.163 0 16c0 12 16 26 16 26s16-14 16-26C32 7.163 24.837 0 16 0z" fill="#3b82f6"/>
            <circle cx="16" cy="16" r="6" fill="white"/>
          </svg>
        `;
        const markerImage = new window.kakao.maps.MarkerImage(
          'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(redMarkerSvg),
          new window.kakao.maps.Size(32, 42),
          { offset: new window.kakao.maps.Point(16, 42) }
        );

        items.forEach((item) => {
          const position = new window.kakao.maps.LatLng(item.lat, item.lng);
          const marker = new window.kakao.maps.Marker({
            position,
            map: mapInstance.current,
            image: markerImage,
          });

          const infoContent = `
            <div style="padding:8px;font-size:13px;max-width:220px;">
              <strong>${item.svcnm}</strong><br/>
              ${item.placenm ?? ''}<br/>
              상태: ${item.svcstatnm ?? '-'}<br/>
              ${item.distanceKm !== null && item.distanceKm !== undefined ? `거리: ${item.distanceKm}km<br/>` : ''}
              <a href="${item.applyUrl}" target="_blank">예약 페이지 이동</a>
            </div>
          `;
          const infoWindow = new window.kakao.maps.InfoWindow({ content: infoContent });

          window.kakao.maps.event.addListener(marker, 'click', () => {
            infoWindow.open(mapInstance.current, marker);
          });

          markersRef.current.push(marker);
          bounds.extend(position);
        });

        if (myLocation) {
          bounds.extend(new window.kakao.maps.LatLng(myLocation.lat, myLocation.lng));
        }

        mapInstance.current.setBounds(bounds);
      }
    } catch (e) {
      setError('검색 중 오류가 발생했어요: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleStatusFilter = (status) => {
    setStatusFilter((prev) => ({ ...prev, [status]: !prev[status] }));
  };

  const togglePlace = (placeName) => {
    setExpandedPlaces((prev) => ({ ...prev, [placeName]: !prev[placeName] }));
  };

  const filteredResults = useMemo(
    () => results.filter((item) => statusFilter[item.svcstatnm]),
    [results, statusFilter]
  );

  const groupedByPlace = useMemo(() => {
    const groups = {};
    filteredResults.forEach((item) => {
      const key = item.placenm || '기타';
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });
    return groups;
  }, [filteredResults]);

  return {
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
  };
}
