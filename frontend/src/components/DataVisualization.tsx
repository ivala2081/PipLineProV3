import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  previousValue?: string | number;
  format?: 'currency' | 'percentage' | 'number';
  currency?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
  className?: string;
}

interface ProgressRingProps {
  percentage: number;
  size?: 'sm' | 'md' | 'lg';
  color?: 'gray' | 'green' | 'red' | 'slate';
  strokeWidth?: number;
  showLabel?: boolean;
  label?: string;
}

interface MiniChartProps {
  data: number[];
  type?: 'line' | 'bar';
  color?: string;
  height?: number;
  showGrid?: boolean;
}

// Enhanced Metric Card with Better Visual Hierarchy
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  previousValue,
  format = 'number',
  currency = '₺',
  trend,
  trendValue,
  className = ''
}) => {
  const formatValue = (val: string | number) => {
    if (format === 'currency') {
      return `${currency}${Number(val).toLocaleString()}`;
    }
    if (format === 'percentage') {
      return `${val}%`;
    }
    return Number(val).toLocaleString();
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-emerald-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-slate-400" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-emerald-600 bg-emerald-50';
      case 'down':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-slate-600 bg-slate-50';
    }
  };

  return (
    <div className={`
      bg-white 
      rounded-xl 
      p-6 
      border 
      border-slate-200 
      shadow-sm 
      hover:shadow-md 
      transition-all 
      duration-200 
      group
      ${className}
    `}>
      {/* Title */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="professional-label">
          {title}
        </h3>
        {trend && (
          <div className={`
            flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium
            ${getTrendColor()}
          `}>
            {getTrendIcon()}
            {trendValue && `${trendValue}%`}
          </div>
        )}
      </div>

      {/* Main Value */}
      <div className="mb-2">
        <div className="professional-metric-value">
          {formatValue(value)}
        </div>
        {previousValue && (
          <div className="text-sm text-slate-500">
            Previous: {formatValue(previousValue)}
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full bg-slate-600 rounded-full transform scale-x-0 group-hover:scale-x-100 transition-transform duration-1000 origin-left" />
      </div>
    </div>
  );
};

// Animated Progress Ring
export const ProgressRing: React.FC<ProgressRingProps> = ({
  percentage,
  size = 'md',
  color = 'gray',
  strokeWidth = 8,
  showLabel = true,
  label
}) => {
  const sizeMap = {
    sm: { width: 60, height: 60, radius: 26 },
    md: { width: 80, height: 80, radius: 36 },
    lg: { width: 120, height: 120, radius: 56 }
  };

  const colorMap = {
    gray: '#6b7280',
    green: '#059669',
    red: '#dc2626',
    slate: '#64748b'
  };

  const { width, height, radius } = sizeMap[size];
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg
        width={width}
        height={height}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={width / 2}
          cy={height / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={width / 2}
          cy={height / 2}
          r={radius}
          stroke={colorMap[color]}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      {showLabel && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">
              {percentage}%
            </div>
            {label && (
              <div className="text-xs text-gray-500 mt-1">
                {label}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Mini Sparkline Chart
export const MiniChart: React.FC<MiniChartProps> = ({
  data,
  type = 'line',
  color = '#3b82f6',
  height = 40,
  showGrid = false
}) => {
  if (!data.length) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = ((max - value) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="w-full" style={{ height }}>
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="overflow-visible"
      >
        {showGrid && (
          <defs>
            <pattern
              id="grid"
              width="10"
              height="10"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 10 0 L 0 0 0 10"
                fill="none"
                stroke="#f3f4f6"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>
        )}
        
        {showGrid && (
          <rect width="100" height="100" fill="url(#grid)" />
        )}
        
        {type === 'line' ? (
          <>
            {/* Area fill */}
            <path
              d={`M 0,100 L ${points} L 100,100 Z`}
              fill={`${color}20`}
              className="transition-all duration-500"
            />
            {/* Line */}
            <polyline
              points={points}
              fill="none"
              stroke={color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="transition-all duration-500"
            />
          </>
        ) : (
          // Bar chart
          data.map((value, index) => {
            const barWidth = 80 / data.length;
            const barHeight = ((value - min) / range) * 100;
            const x = (index / data.length) * 100 + 10;
            const y = 100 - barHeight;
            
            return (
              <rect
                key={index}
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={color}
                rx="1"
                className="transition-all duration-500"
              />
            );
          })
        )}
      </svg>
    </div>
  );
};

export default { MetricCard, ProgressRing, MiniChart };
