import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'shimmer' | 'none';
}

/**
 * PremiumSkeleton - Advanced loading skeleton with shimmer effect
 * 
 * Features:
 * - Smooth shimmer animation (looks faster than spinners)
 * - Multiple variants (text, circular, rectangular, rounded)
 * - Customizable size and animation
 * - Shows actual content layout while loading
 * - More professional than spinning loaders
 * 
 * Usage:
 * <PremiumSkeleton variant="text" width="200px" height="20px" />
 * <PremiumSkeleton variant="circular" width="40px" height="40px" />
 */
export const PremiumSkeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rectangular',
  width,
  height,
  animation = 'shimmer'
}) => {
  const baseClasses = 'bg-gray-200 relative overflow-hidden';
  
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
    rounded: 'rounded-lg'
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    shimmer: '',
    none: ''
  };

  const style: React.CSSProperties = {
    width: width || '100%',
    height: height || (variant === 'text' ? '1rem' : '100%'),
  };

  return (
    <div
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${animationClasses[animation]}
        ${className}
      `}
      style={style}
      role="status"
      aria-label="Loading..."
    >
      {animation === 'shimmer' && (
        <div 
          className="absolute inset-0 animate-shimmer"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.6) 50%, transparent 100%)',
          }}
        />
      )}
    </div>
  );
};

/**
 * CardSkeleton - Pre-built card skeleton
 */
export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white rounded-lg p-6 shadow-sm border border-gray-200 ${className}`}>
    <div className="flex items-center justify-between mb-4">
      <PremiumSkeleton variant="text" width="120px" height="20px" />
      <PremiumSkeleton variant="circular" width="24px" height="24px" />
    </div>
    <PremiumSkeleton variant="text" width="180px" height="36px" className="mb-2" />
    <PremiumSkeleton variant="text" width="140px" height="16px" />
  </div>
);

/**
 * MetricCardSkeleton - Skeleton for metric cards
 */
export const MetricCardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`bg-white rounded-lg p-6 shadow-premium border border-gray-100 ${className}`}>
    <div className="flex items-center justify-between mb-4">
      <PremiumSkeleton variant="text" width="100px" height="16px" />
      <PremiumSkeleton variant="rounded" width="40px" height="40px" />
    </div>
    <PremiumSkeleton variant="text" width="140px" height="32px" className="mb-2" />
    <div className="flex items-center gap-2">
      <PremiumSkeleton variant="text" width="60px" height="20px" />
      <PremiumSkeleton variant="text" width="80px" height="14px" />
    </div>
  </div>
);

/**
 * TableRowSkeleton - Skeleton for table rows
 */
export const TableRowSkeleton: React.FC<{ columns?: number; className?: string }> = ({ 
  columns = 4, 
  className = '' 
}) => (
  <div className={`flex items-center gap-4 py-4 border-b border-gray-100 ${className}`}>
    {Array.from({ length: columns }).map((_, i) => (
      <PremiumSkeleton 
        key={i} 
        variant="text" 
        width={i === 0 ? '120px' : '80px'} 
        height="16px" 
      />
    ))}
  </div>
);

/**
 * ChartSkeleton - Skeleton for charts
 */
export const ChartSkeleton: React.FC<{ className?: string; height?: string }> = ({ 
  className = '',
  height = '300px'
}) => (
  <div className={`bg-white rounded-lg p-6 shadow-sm border border-gray-200 ${className}`}>
    <div className="flex items-center justify-between mb-6">
      <PremiumSkeleton variant="text" width="150px" height="20px" />
      <PremiumSkeleton variant="rounded" width="100px" height="32px" />
    </div>
    <div className="flex items-end justify-between gap-2" style={{ height }}>
      {Array.from({ length: 12 }).map((_, i) => (
        <PremiumSkeleton 
          key={i} 
          variant="rounded" 
          width="100%" 
          height={`${Math.random() * 60 + 40}%`} 
        />
      ))}
    </div>
  </div>
);

/**
 * DashboardSkeleton - Full dashboard skeleton layout
 */
export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6 p-6">
    {/* Header */}
    <div className="flex items-center justify-between">
      <PremiumSkeleton variant="text" width="200px" height="32px" />
      <PremiumSkeleton variant="rounded" width="120px" height="40px" />
    </div>

    {/* Metrics Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCardSkeleton />
      <MetricCardSkeleton />
      <MetricCardSkeleton />
      <MetricCardSkeleton />
    </div>

    {/* Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ChartSkeleton />
      <ChartSkeleton />
    </div>

    {/* Table */}
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <PremiumSkeleton variant="text" width="150px" height="20px" className="mb-4" />
      <div className="space-y-2">
        <TableRowSkeleton columns={5} />
        <TableRowSkeleton columns={5} />
        <TableRowSkeleton columns={5} />
        <TableRowSkeleton columns={5} />
        <TableRowSkeleton columns={5} />
      </div>
    </div>
  </div>
);

export default PremiumSkeleton;

