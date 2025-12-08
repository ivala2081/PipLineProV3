import React, { useRef, useEffect, useState } from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  showArea?: boolean;
  showDots?: boolean;
  showTooltip?: boolean;
  className?: string;
}

/**
 * Sparkline - Tiny inline chart for showing trends
 * 
 * Features:
 * - Smooth line chart with optional area fill
 * - Interactive hover tooltip
 * - Auto-scaling to data range
 * - Optional dots at data points
 * - Color-coded positive/negative
 * - Responsive SVG
 * 
 * Usage:
 * <Sparkline data={[1, 5, 3, 7, 4]} color="#10b981" showArea />
 */
export const Sparkline: React.FC<SparklineProps> = ({
  data,
  width = 100,
  height = 32,
  color = '#2563eb',
  showArea = true,
  showDots = false,
  showTooltip = true,
  className = ''
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  if (!data || data.length === 0) {
    return null;
  }

  // Calculate min/max for scaling
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1; // Avoid division by zero
  
  // Add padding to the chart (10% on each side)
  const padding = range * 0.1;
  const scaledMin = min - padding;
  const scaledMax = max + padding;
  const scaledRange = scaledMax - scaledMin;

  // Calculate points for the line
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - scaledMin) / scaledRange) * height;
    return { x, y, value };
  });

  // Create path for the line
  const linePath = points
    .map((point, index) => {
      if (index === 0) {
        return `M ${point.x},${point.y}`;
      }
      // Use quadratic bezier curves for smooth line
      const prevPoint = points[index - 1];
      const controlX = (prevPoint.x + point.x) / 2;
      return `Q ${controlX},${prevPoint.y} ${controlX},${point.y} T ${point.x},${point.y}`;
    })
    .join(' ');

  // Create path for the area (if enabled)
  const areaPath = showArea
    ? `${linePath} L ${width},${height} L 0,${height} Z`
    : '';

  // Determine if trend is positive or negative
  const isPositive = data[data.length - 1] >= data[0];
  const autoColor = isPositive ? '#10b981' : '#ef4444';
  const finalColor = color || autoColor;

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!showTooltip || !svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    
    // Find closest point
    const index = Math.round((x / width) * (data.length - 1));
    const clampedIndex = Math.max(0, Math.min(data.length - 1, index));
    
    setHoveredIndex(clampedIndex);
    setTooltipPos({ x: points[clampedIndex].x, y: points[clampedIndex].y });
  };

  const handleMouseLeave = () => {
    setHoveredIndex(null);
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="cursor-crosshair"
        style={{ overflow: 'visible' }}
      >
        {/* Area fill */}
        {showArea && (
          <path
            d={areaPath}
            fill={finalColor}
            opacity={0.15}
          />
        )}

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke={finalColor}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Dots at data points */}
        {showDots && points.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r={hoveredIndex === index ? 4 : 2}
            fill={finalColor}
            className="transition-all duration-200"
          />
        ))}

        {/* Hover indicator */}
        {showTooltip && hoveredIndex !== null && (
          <>
            {/* Vertical line */}
            <line
              x1={tooltipPos.x}
              y1={0}
              x2={tooltipPos.x}
              y2={height}
              stroke={finalColor}
              strokeWidth={1}
              strokeDasharray="2,2"
              opacity={0.5}
            />
            {/* Hover dot */}
            <circle
              cx={tooltipPos.x}
              cy={tooltipPos.y}
              r={4}
              fill={finalColor}
              stroke="white"
              strokeWidth={2}
            />
          </>
        )}
      </svg>

      {/* Tooltip */}
      {showTooltip && hoveredIndex !== null && (
        <div
          className="absolute z-50 bg-slate-900 text-white text-xs px-2 py-1 rounded shadow-lg pointer-events-none whitespace-nowrap"
          style={{
            left: tooltipPos.x,
            top: tooltipPos.y - 30,
            transform: 'translateX(-50%)'
          }}
        >
          {data[hoveredIndex].toLocaleString()}
        </div>
      )}
    </div>
  );
};

/**
 * MiniSparkline - Tiny version for inline use
 */
export const MiniSparkline: React.FC<Omit<SparklineProps, 'width' | 'height'>> = (props) => (
  <Sparkline {...props} width={60} height={20} showDots={false} showTooltip={false} />
);

/**
 * TrendSparkline - With automatic positive/negative coloring
 */
export const TrendSparkline: React.FC<Omit<SparklineProps, 'color'>> = (props) => {
  const { data } = props;
  const isPositive = data && data.length > 0 && data[data.length - 1] >= data[0];
  const color = isPositive ? '#10b981' : '#ef4444';
  
  return <Sparkline {...props} color={color} />;
};

export default Sparkline;

