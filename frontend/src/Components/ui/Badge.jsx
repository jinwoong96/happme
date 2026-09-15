import { cn } from '../../lib/utils';

const colorMap = {
  인기: 'bg-red-100 text-red-500',
  마감임박: 'bg-orange-100 text-orange-500',
  신규: 'bg-green-100 text-green-500',
  고육: 'bg-blue-100 text-blue-500',
  취업: 'bg-purple-100 text-purple-500',
};

// 라벨 텍스트에 맞는 색상을 자동으로 골라주는 작은 뱃지.
export default function Badge({ label, className }) {
  return (
    <span className={cn('text-xs font-medium px-2 py-0.5 rounded-full', colorMap[label] || 'bg-gray-100 text-gray-500', className)}>
      {label}
    </span>
  );
}
