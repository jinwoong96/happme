import { cn } from '../../lib/utils';

// 공용 텍스트 입력 필드.
export default function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        'w-full px-4 py-3.5 rounded-2xl border border-gray-200 bg-white text-sm outline-none focus:border-blue-400 placeholder:text-gray-400',
        className
      )}
      {...props}
    />
  );
}
