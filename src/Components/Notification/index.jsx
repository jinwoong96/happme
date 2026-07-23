import { Bell } from 'lucide-react';

// 상단 알림 종 아이콘. 안읽은 개수(count)가 있으면 빨간 배지를 표시한다(9개 초과는 "9+").
export default function NotificationBell({ count = 0 }) {
  return (
    <button className="relative p-1">
      <Bell size={22} className="text-gray-600" />
      {count > 0 && (
        <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">
          {count > 9 ? '9+' : count}
        </span>
      )}
    </button>
  );
}
