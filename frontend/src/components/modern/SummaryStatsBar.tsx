import React from 'react';
import { QuickStatsCard } from './QuickStatsCard';
import { SkeletonLoader } from './SkeletonLoader';

interface SummaryStat {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  change?: string;
  trend?: 'up' | 'down';
}

interface SummaryStatsBarProps {
  stats: SummaryStat[];
  loading?: boolean;
  onStatClick?: (statIndex: number) => void;
}

export const SummaryStatsBar: React.FC<SummaryStatsBarProps> = ({
  stats,
  loading = false,
  onStatClick,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <SkeletonLoader key={i} className="h-32" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <div key={index}>
          <QuickStatsCard
            label={stat.label}
            value={stat.value}
            icon={stat.icon}
            change={stat.change}
            trend={stat.trend}
            loading={false}
          />
        </div>
      ))}
    </div>
  );
};

export default SummaryStatsBar;

