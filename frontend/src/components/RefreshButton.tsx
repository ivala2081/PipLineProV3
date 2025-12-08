import React from 'react';
import { RefreshCw } from 'lucide-react';

interface RefreshButtonProps {
  onRefresh: () => void;
  loading?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'outline';
}

const RefreshButton: React.FC<RefreshButtonProps> = ({
  onRefresh,
  loading = false,
  className = '',
  size = 'md',
  variant = 'primary'
}) => {
  const sizeClasses = {
    sm: 'p-2 text-sm',
    md: 'p-2.5 text-base',
    lg: 'p-3 text-lg'
  };

  const variantClasses = {
    primary: 'bg-gray-600 hover:bg-gray-700 text-white shadow-md hover:shadow-lg',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white shadow-md hover:shadow-lg',
    outline: 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 hover:border-gray-400 shadow-sm hover:shadow-md'
  };

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6'
  };

  return (
    <button
      onClick={onRefresh}
      disabled={loading}
      className={`
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        rounded-xl font-medium transition-all duration-300 
        hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed
        disabled:transform-none flex items-center gap-2
        ${className}
      `}
      title={loading ? 'Refreshing...' : 'Refresh data'}
    >
      <RefreshCw 
        className={`${iconSizes[size]} ${loading ? 'animate-spin' : ''}`} 
      />
      {size !== 'sm' && (
        <span className="hidden sm:inline">
          {loading ? 'Refreshing...' : 'Refresh'}
        </span>
      )}
    </button>
  );
};

export default RefreshButton;
