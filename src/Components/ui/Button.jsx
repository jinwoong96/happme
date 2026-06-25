import { cn } from '../../lib/utils';

export default function Button({ children, variant = 'primary', className, ...props }) {
  const base = 'w-full py-4 rounded-2xl font-semibold text-base transition-opacity active:opacity-80';
  const variants = {
    primary: 'bg-blue-500 text-white',
    outline: 'border border-blue-500 text-blue-500 bg-white',
    ghost: 'text-gray-500 bg-transparent',
  };

  return (
    <button className={cn(base, variants[variant], className)} {...props}>
      {children}
    </button>
  );
}
