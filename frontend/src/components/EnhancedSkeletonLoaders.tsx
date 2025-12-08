import React from 'react';
import { LucideIcon } from 'lucide-react';

// Base skeleton component with enhanced animations
interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  animate?: 'pulse' | 'wave' | 'shimmer';
  delay?: number;
}

const Skeleton: React.FC<SkeletonProps> = ({ 
  className = '', 
  width, 
  height, 
  rounded = 'md',
  animate = 'shimmer',
  delay = 0
}) => {
  const roundedClasses = {
    none: '',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full'
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-pulse',
    shimmer: 'skeleton-shimmer'
  };

  return (
    <div
      className={`bg-gray-200 ${roundedClasses[rounded]} ${animationClasses[animate]} ${className}`}
      style={{
        width: width,
        height: height,
        animationDelay: `${delay}ms`
      }}
    />
  );
};

// Enhanced Metrics Card Skeleton - matches StandardMetricsCard structure
export const MetricsCardSkeleton: React.FC<{
  variant?: 'default' | 'gradient' | 'minimal' | 'compact';
  delay?: number;
}> = ({ variant = 'default', delay = 0 }) => {
  const baseDelay = delay;

  if (variant === 'compact') {
    return (
      <div className="bg-white rounded-md border border-gray-200 p-2.5 animate-pulse" style={{ animationDelay: `${baseDelay}ms` }}>
        <div className="flex items-center gap-2">
          <Skeleton className="w-6 h-6" rounded="md" delay={baseDelay + 100} />
          <div className="flex-1 min-w-0">
            <Skeleton className="h-3 w-20 mb-1" delay={baseDelay + 200} />
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-16" delay={baseDelay + 300} />
              <Skeleton className="h-3 w-8" delay={baseDelay + 400} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'minimal') {
    return (
      <div className="bg-white rounded-md border border-gray-200 p-3 animate-pulse" style={{ animationDelay: `${baseDelay}ms` }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="w-6 h-6" rounded="md" delay={baseDelay + 100} />
            <div>
              <Skeleton className="h-3 w-20 mb-1" delay={baseDelay + 200} />
              <Skeleton className="h-4 w-24" delay={baseDelay + 300} />
            </div>
          </div>
          <Skeleton className="h-3 w-12" delay={baseDelay + 400} />
        </div>
      </div>
    );
  }

  if (variant === 'gradient') {
    return (
      <div className="bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg shadow-sm p-4 animate-pulse" style={{ animationDelay: `${baseDelay}ms` }}>
        <div className="flex items-center justify-between mb-3">
          <Skeleton className="w-8 h-8 bg-white/20" rounded="lg" delay={baseDelay + 100} />
          <Skeleton className="h-4 w-16 bg-white/20" rounded="full" delay={baseDelay + 200} />
        </div>
        <div className="space-y-0.5">
          <Skeleton className="h-3 w-24 bg-white/20" delay={baseDelay + 300} />
          <Skeleton className="h-5 w-32 bg-white/20" delay={baseDelay + 400} />
          <Skeleton className="h-3 w-20 bg-white/20" delay={baseDelay + 500} />
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 animate-pulse" style={{ animationDelay: `${baseDelay}ms` }}>
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="w-8 h-8" rounded="lg" delay={baseDelay + 100} />
        <Skeleton className="h-4 w-16" rounded="full" delay={baseDelay + 200} />
      </div>
      <div className="space-y-0.5">
        <Skeleton className="h-3 w-24" delay={baseDelay + 300} />
        <Skeleton className="h-5 w-32" delay={baseDelay + 400} />
        <Skeleton className="h-3 w-20" delay={baseDelay + 500} />
      </div>
    </div>
  );
};

// Enhanced Table Skeleton with realistic structure
export const TableSkeleton: React.FC<{
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  delay?: number;
}> = ({ rows = 5, columns = 5, showHeader = true, delay = 0 }) => {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden animate-pulse" style={{ animationDelay: `${delay}ms` }}>
      {/* Table Header */}
      {showHeader && (
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {[...Array(columns)].map((_, i) => (
              <Skeleton key={i} className="h-4 w-20" delay={delay + (i * 50)} />
            ))}
          </div>
        </div>
      )}
      
      {/* Table Rows */}
      <div className="divide-y divide-gray-200">
        {[...Array(rows)].map((_, rowIndex) => (
          <div key={rowIndex} className="px-6 py-4">
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
              {[...Array(columns)].map((_, colIndex) => (
                <div key={colIndex} className="flex items-center">
                  {colIndex === 0 ? (
                    <div className="flex items-center gap-3">
                      <Skeleton className="w-8 h-8" rounded="full" delay={delay + (rowIndex * 100) + (colIndex * 50)} />
                      <Skeleton className="h-4 w-24" delay={delay + (rowIndex * 100) + (colIndex * 50) + 25} />
                    </div>
                  ) : (
                    <Skeleton className="h-4 w-16" delay={delay + (rowIndex * 100) + (colIndex * 50)} />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Enhanced Chart Skeleton with realistic chart elements
export const ChartSkeleton: React.FC<{
  type?: 'line' | 'bar' | 'pie' | 'area';
  showLegend?: boolean;
  delay?: number;
}> = ({ type = 'line', showLegend = true, delay = 0 }) => {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 animate-pulse" style={{ animationDelay: `${delay}ms` }}>
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Skeleton className="h-6 w-32 mb-2" delay={delay + 100} />
          <Skeleton className="h-4 w-48" delay={delay + 200} />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20" rounded="lg" delay={delay + 300} />
          <Skeleton className="h-8 w-8" rounded="lg" delay={delay + 350} />
        </div>
      </div>

      {/* Chart Area */}
      <div className="h-80 bg-gray-50 rounded-lg p-4 relative overflow-hidden">
        {type === 'pie' ? (
          <div className="flex items-center justify-center h-full">
            <Skeleton className="w-48 h-48" rounded="full" delay={delay + 400} />
          </div>
        ) : (
          <div className="h-full flex items-end justify-between gap-2">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="flex-1 flex flex-col justify-end">
                <Skeleton 
                  className="w-full" 
                  height={`${Math.random() * 60 + 20}%`}
                  delay={delay + 400 + (i * 50)}
                />
              </div>
            ))}
          </div>
        )}
        
        {/* Chart axes */}
        {type !== 'pie' && (
          <>
            <div className="absolute bottom-4 left-4 right-4 h-px bg-gray-300"></div>
            <div className="absolute bottom-4 left-4 top-4 w-px bg-gray-300"></div>
          </>
        )}
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="mt-4 flex flex-wrap gap-4">
          {[...Array(type === 'pie' ? 5 : 3)].map((_, i) => (
            <div key={i} className="flex items-center gap-2">
              <Skeleton className="w-3 h-3" rounded="full" delay={delay + 600 + (i * 50)} />
              <Skeleton className="h-4 w-16" delay={delay + 625 + (i * 50)} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Page-specific skeleton layouts
export const DashboardPageSkeleton: React.FC = () => (
  <div className="space-y-8">
    {/* Page Header */}
    <div className="bg-gradient-to-r from-gray-50 via-white to-purple-50 rounded-2xl p-8 border border-gray-100 shadow-sm animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="w-12 h-12" rounded="xl" />
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-5 w-64" />
          </div>
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-10 w-32" rounded="lg" delay={100} />
          <Skeleton className="h-10 w-10" rounded="lg" delay={150} />
        </div>
      </div>
    </div>

    {/* Metrics Cards Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <MetricsCardSkeleton key={i} delay={i * 100} />
      ))}
    </div>

    {/* Charts Section */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <ChartSkeleton type="line" delay={200} />
      <ChartSkeleton type="bar" delay={300} />
    </div>

    {/* Data Table */}
    <TableSkeleton rows={6} columns={6} delay={400} />
  </div>
);

export const ClientsPageSkeleton: React.FC = () => (
  <div className="space-y-8">
    {/* Financial Overview Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <MetricsCardSkeleton key={i} delay={i * 100} />
      ))}
    </div>

    {/* Client Insights */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <ChartSkeleton type="pie" delay={200} />
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-4 border border-gray-200 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10" rounded="full" delay={300 + (i * 50)} />
                <div>
                  <Skeleton className="h-4 w-24 mb-1" delay={325 + (i * 50)} />
                  <Skeleton className="h-3 w-16" delay={350 + (i * 50)} />
                </div>
              </div>
              <Skeleton className="h-6 w-20" delay={375 + (i * 50)} />
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Transactions Table */}
    <TableSkeleton rows={8} columns={7} delay={500} />
  </div>
);

export const LedgerPageSkeleton: React.FC = () => (
  <div className="space-y-8">
    {/* PSP Overview Cards */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <MetricsCardSkeleton key={i} delay={i * 100} />
      ))}
    </div>

    {/* PSP Cards Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200 animate-pulse" style={{ animationDelay: `${200 + (i * 100)}ms` }}>
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <Skeleton className="w-14 h-14" rounded="2xl" delay={250 + (i * 100)} />
              <div>
                <Skeleton className="h-6 w-20 mb-2" delay={275 + (i * 100)} />
                <Skeleton className="h-4 w-32" delay={300 + (i * 100)} />
              </div>
            </div>
          </div>
          <div className="space-y-4">
            {[...Array(3)].map((_, j) => (
              <div key={j} className="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
                <Skeleton className="h-4 w-24" delay={325 + (i * 100) + (j * 25)} />
                <Skeleton className="h-4 w-16" delay={350 + (i * 100) + (j * 25)} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const AnalyticsPageSkeleton: React.FC = () => (
  <div className="space-y-8">
    {/* Key Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <MetricsCardSkeleton key={i} delay={i * 100} />
      ))}
    </div>

    {/* Analytics Charts */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <ChartSkeleton type="pie" showLegend={true} delay={200} />
      <ChartSkeleton type="bar" showLegend={true} delay={300} />
    </div>

    <div className="grid grid-cols-1 gap-8">
      <ChartSkeleton type="area" showLegend={true} delay={400} />
    </div>
  </div>
);

// Progressive Loading Component
export const ProgressiveLoader: React.FC<{
  steps: string[];
  currentStep: number;
  className?: string;
}> = ({ steps, currentStep, className = '' }) => (
  <div className={`bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center ${className}`}>
    <div className="w-16 h-16 mx-auto mb-6">
      <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-100 border-t-gray-600"></div>
    </div>
    <h3 className="text-lg font-semibold text-gray-900 mb-2">Loading...</h3>
    <p className="text-gray-600 mb-4">{steps[currentStep] || 'Please wait...'}</p>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className="bg-gray-600 h-2 rounded-full transition-all duration-500"
        style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
      ></div>
    </div>
    <p className="text-sm text-gray-500 mt-2">
      Step {currentStep + 1} of {steps.length}
    </p>
  </div>
);

export default Skeleton;
