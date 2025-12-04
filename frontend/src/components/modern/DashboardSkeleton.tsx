import React from 'react';

/**
 * Reusable Skeleton Components for Dashboard
 * These provide visual feedback while content is loading
 */

// Base Skeleton Line Component
export const SkeletonLine: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-slate-200 rounded ${className}`}></div>
);

// Quick Stats Card Skeleton
export const QuickStatsSkeleton: React.FC = () => (
  <div className="dashboard-grid">
    {[...Array(4)].map((_, i) => (
      <div key={i} className="dashboard-card metric-card border-0 shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="w-12 h-12 bg-slate-200 rounded-xl animate-pulse"></div>
          <div className="w-16 h-4 bg-slate-200 rounded animate-pulse"></div>
        </div>
        <div className="space-y-2">
          <div className="h-8 bg-slate-200 rounded animate-pulse w-3/4"></div>
          <div className="h-4 bg-slate-200 rounded animate-pulse w-1/2"></div>
        </div>
      </div>
    ))}
  </div>
);

// Chart Skeleton
export const ChartSkeleton: React.FC = () => (
  <div className="dashboard-card dashboard-glass border-0 shadow-lg">
    <div className="p-6 pb-4">
      <div className="flex items-center justify-between mb-6">
        <div className="space-y-2 flex-1">
          <div className="h-6 bg-slate-200 rounded animate-pulse w-1/3"></div>
          <div className="h-4 bg-slate-200 rounded animate-pulse w-1/2"></div>
        </div>
        <div className="flex items-center gap-4">
          <div className="w-32 h-8 bg-slate-200 rounded animate-pulse"></div>
          <div className="w-32 h-8 bg-slate-200 rounded animate-pulse"></div>
          <div className="w-20 h-6 bg-slate-200 rounded-full animate-pulse"></div>
        </div>
      </div>
    </div>
    <div className="px-6 pb-6">
      <div className="h-96 bg-slate-100 rounded-lg animate-pulse relative overflow-hidden">
        {/* Shimmer effect */}
        <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
        {/* Fake chart bars */}
        <div className="flex items-end justify-around h-full p-8 gap-2">
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="bg-slate-200 rounded-t w-full"
              style={{ height: `${Math.random() * 60 + 40}%` }}
            ></div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

// Financial Performance Card Skeleton
export const FinancialPerformanceCardSkeleton: React.FC<{ title?: string }> = ({ 
  title = 'Performance' 
}) => (
  <div className="dashboard-card dashboard-glass border-0 shadow-lg">
    <div className="p-6 pb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-slate-200 rounded-xl animate-pulse"></div>
          <div className="h-5 bg-slate-200 rounded animate-pulse w-32"></div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-slate-200 rounded-full animate-pulse"></div>
          <div className="w-12 h-3 bg-slate-200 rounded animate-pulse"></div>
        </div>
      </div>
    </div>
    <div className="px-6 pb-6">
      <div className="space-y-4">
        {/* Payment Methods Section */}
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex items-center justify-between py-3 px-4 bg-slate-50 rounded border">
              <div className="flex items-center gap-3 flex-1">
                <div className="w-4 h-4 bg-slate-200 rounded animate-pulse"></div>
                <div className="h-3 bg-slate-200 rounded animate-pulse w-24"></div>
              </div>
              <div className="space-y-1">
                <div className="h-4 bg-slate-200 rounded animate-pulse w-20 ml-auto"></div>
                <div className="h-3 bg-slate-200 rounded animate-pulse w-16 ml-auto"></div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Transaction Flow Section */}
        <div className="space-y-2 pt-2 border-t-2 border-slate-300">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center justify-between py-3 px-4 bg-slate-50 rounded border">
              <div className="flex items-center gap-3 flex-1">
                <div className="w-4 h-4 bg-slate-200 rounded animate-pulse"></div>
                <div className="h-3 bg-slate-200 rounded animate-pulse w-20"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded animate-pulse w-24 ml-auto"></div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Navigation Controls */}
      <div className="mt-4 pt-4 border-t border-slate-200">
        <div className="flex items-center justify-center gap-3">
          <div className="h-8 w-8 bg-slate-200 rounded animate-pulse"></div>
          <div className="h-4 bg-slate-200 rounded animate-pulse flex-1 max-w-md"></div>
          <div className="h-8 w-8 bg-slate-200 rounded animate-pulse"></div>
        </div>
      </div>
    </div>
  </div>
);

// Full Dashboard Skeleton (for initial load)
export const FullDashboardSkeleton: React.FC = () => (
  <main className="flex-1 bg-gradient-to-br from-slate-50 via-white to-slate-100 min-h-screen">
    <div className="px-8 py-8">
      <div className="space-y-8">
        
        {/* Header Section */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-2">
            <div className="h-10 bg-slate-200 rounded animate-pulse w-64"></div>
            <div className="h-5 bg-slate-200 rounded animate-pulse w-96"></div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="w-32 h-10 bg-slate-200 rounded-lg animate-pulse"></div>
            <div className="w-24 h-10 bg-slate-200 rounded-lg animate-pulse"></div>
            <div className="w-24 h-10 bg-slate-200 rounded-lg animate-pulse"></div>
            <div className="w-24 h-10 bg-slate-200 rounded-lg animate-pulse"></div>
          </div>
        </div>

        {/* Quick Stats */}
        <QuickStatsSkeleton />

        {/* Main Content */}
        <div className="space-y-8">
          {/* Chart */}
          <ChartSkeleton />

          {/* Financial Performance Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <FinancialPerformanceCardSkeleton title="Daily" />
            <FinancialPerformanceCardSkeleton title="Monthly" />
            <FinancialPerformanceCardSkeleton title="Total" />
          </div>
        </div>

      </div>
    </div>
  </main>
);

// Add shimmer animation to global CSS
const shimmerStyles = `
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 2s infinite;
}
`;

// Export a function to inject styles (call once in your app)
export const injectShimmerStyles = () => {
  if (typeof document !== 'undefined' && !document.getElementById('shimmer-styles')) {
    const style = document.createElement('style');
    style.id = 'shimmer-styles';
    style.textContent = shimmerStyles;
    document.head.appendChild(style);
  }
};

