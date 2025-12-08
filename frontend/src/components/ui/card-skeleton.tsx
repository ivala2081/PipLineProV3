import { Skeleton } from "./skeleton"

interface CardSkeletonProps {
  showHeader?: boolean
  showFooter?: boolean
  lines?: number
}

export function CardSkeleton({ 
  showHeader = true, 
  showFooter = false, 
  lines = 3 
}: CardSkeletonProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {showHeader && (
        <div className="mb-4">
          <Skeleton className="h-6 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      )}
      
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
      
      {showFooter && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <Skeleton className="h-8 w-24" />
        </div>
      )}
    </div>
  )
}
