import { Skeleton } from "./skeleton"

interface ChartSkeletonProps {
  height?: number
  showLegend?: boolean
}

export function ChartSkeleton({ height = 300, showLegend = true }: ChartSkeletonProps) {
  return (
    <div className="w-full">
      {/* Chart Area */}
      <div 
        className="relative rounded-lg bg-slate-50 p-4"
        style={{ height: `${height}px` }}
      >
        {/* Y-axis labels */}
        <div className="absolute left-0 top-4 space-y-8">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-3 w-8" />
          ))}
        </div>
        
        {/* Chart bars/lines */}
        <div className="ml-12 flex h-full items-end space-x-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton 
              key={i} 
              className="w-8 bg-slate-300" 
              style={{ height: `${Math.random() * 60 + 20}%` }}
            />
          ))}
        </div>
        
        {/* X-axis labels */}
        <div className="absolute bottom-0 left-12 right-0 flex justify-between">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-3 w-12" />
          ))}
        </div>
      </div>
      
      {/* Legend */}
      {showLegend && (
        <div className="mt-4 flex flex-wrap gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center space-x-2">
              <Skeleton className="h-3 w-3 rounded-full" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
