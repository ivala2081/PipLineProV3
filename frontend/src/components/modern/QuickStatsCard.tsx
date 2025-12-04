import React from 'react';
import { Card, CardContent } from '../ui/card';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { CountUp } from '../ui/CountUp';
import { MetricCardSkeleton } from '../ui/PremiumSkeleton';
import { TrendSparkline } from '../ui/Sparkline';

interface QuickStatsCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  change?: string;
  trend?: 'up' | 'down';
  loading?: boolean;
  sparklineData?: number[]; // Optional 7-day trend data
  showGlass?: boolean; // Enable glassmorphism effect
}

/**
 * Enhanced QuickStatsCard with Phase 1 & 2 Premium Features:
 * - CountUp animation for numbers
 * - Premium hover effects (lift up)
 * - Layered shadows for depth
 * - Shimmer loading states
 * - Trend indicators with icons
 * - Sparkline mini-charts (Phase 2)
 * - Glassmorphism effects (Phase 2)
 */
export const QuickStatsCard: React.FC<QuickStatsCardProps> = ({
  label,
  value,
  icon: Icon,
  change,
  trend = 'up',
  loading = false,
  sparklineData,
  showGlass = false
}) => {
  // Extract numeric value for CountUp animation
  const getNumericValue = (val: string | number): number | null => {
    if (typeof val === 'number') return val;
    
    // CRITICAL FIX: Remove currency symbols, thousand separators, and parse
    // Since toLocaleString uses maximumFractionDigits: 0, there are no decimals
    // Keep minus sign for negative numbers, remove all other non-digit characters
    const cleaned = val.toString()
      .replace(/[₺$,₽€£\s,.]/g, '') // Remove currency symbols, spaces, commas, and periods (all thousand separators)
      .trim();
    
    // Handle negative numbers (if original had minus sign)
    const isNegative = val.toString().trim().startsWith('-');
    const finalValue = isNegative ? `-${cleaned}` : cleaned;
    
    const parsed = parseFloat(finalValue);
    return isNaN(parsed) ? null : parsed;
  };

  // Extract prefix/suffix from value
  const getValueParts = (val: string | number) => {
    if (typeof val === 'number') {
      return { prefix: '', suffix: '', numeric: val };
    }
    
    const str = val.toString();
    const hasPercent = str.includes('%');
    const hasCurrency = /[₺$₽€£]/.test(str);
    
    let prefix = '';
    let suffix = '';
    
    if (hasCurrency) {
      const match = str.match(/[₺$₽€£]/);
      if (match) prefix = match[0];
    }
    
    if (hasPercent) suffix = '%';
    
    const numeric = getNumericValue(val);
    
    return { prefix, suffix, numeric };
  };

  if (loading) {
    return <MetricCardSkeleton />;
  }

  const valueParts = getValueParts(value);
  const TrendIcon = trend === 'up' ? TrendingUp : TrendingDown;

  // Glassmorphism class conditionally applied
  const glassClass = showGlass ? 'glass-card-strong glass-hover' : '';

  return (
    <Card className={`dashboard-card metric-card group border-0 shadow-premium card-hover-subtle overflow-hidden relative ${glassClass}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          {/* Icon with subtle background */}
          <div className="w-12 h-12 bg-gradient-to-br from-slate-100 to-slate-50 rounded-xl flex items-center justify-center group-hover:from-slate-200 group-hover:to-slate-100 transition-all duration-300 floating">
            <Icon className="w-6 h-6 text-slate-700" />
          </div>
          
          {/* Trend Badge */}
          {change && (
            <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full transition-all duration-200 ${
              trend === 'up' 
                ? 'bg-green-50 text-green-700 group-hover:bg-green-100' 
                : 'bg-red-50 text-red-700 group-hover:bg-red-100'
            }`}>
              <TrendIcon className="w-3.5 h-3.5" />
              <span className="text-sm font-semibold">
                {change}
              </span>
            </div>
          )}
        </div>
        
        <div className="space-y-2">
          {/* Animated Number with CountUp */}
          <p className="text-3xl font-bold text-slate-900 tracking-tight">
            {valueParts.numeric !== null ? (
              <CountUp 
                end={valueParts.numeric}
                duration={1500}
                decimals={valueParts.suffix === '%' ? 1 : 0}
                prefix={valueParts.prefix}
                suffix={valueParts.suffix}
                separator=","
              />
            ) : (
              value
            )}
          </p>
          
          {/* Label */}
          <p className="text-sm text-slate-600 font-medium">{label}</p>
          
          {/* Sparkline Chart (Phase 2) */}
          {sparklineData && sparklineData.length > 0 && (
            <div className="pt-2 mt-2 border-t border-slate-100">
              <TrendSparkline 
                data={sparklineData}
                width={200}
                height={32}
                showArea={true}
                showTooltip={true}
              />
            </div>
          )}
        </div>
      </CardContent>
      
      {/* Subtle gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/0 to-slate-50/0 group-hover:from-white/30 group-hover:to-slate-50/30 pointer-events-none transition-all duration-300"></div>
    </Card>
  );
};

