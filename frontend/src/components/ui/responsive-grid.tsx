import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface ResponsiveGridProps {
  children: ReactNode
  cols?: {
    default?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }
  gap?: 'sm' | 'md' | 'lg'
  className?: string
}

export function ResponsiveGrid({ 
  children, 
  cols = { default: 1, sm: 2, md: 3, lg: 4 },
  gap = 'md',
  className 
}: ResponsiveGridProps) {
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6'
  }

  const gridCols = {
    default: `grid-cols-${cols.default || 1}`,
    sm: cols.sm ? `sm:grid-cols-${cols.sm}` : '',
    md: cols.md ? `md:grid-cols-${cols.md}` : '',
    lg: cols.lg ? `lg:grid-cols-${cols.lg}` : '',
    xl: cols.xl ? `xl:grid-cols-${cols.xl}` : ''
  }

  return (
    <div
      className={cn(
        'grid',
        gridCols.default,
        gridCols.sm,
        gridCols.md,
        gridCols.lg,
        gridCols.xl,
        gapClasses[gap],
        className
      )}
    >
      {children}
    </div>
  )
}

interface ResponsiveCardProps {
  children: ReactNode
  className?: string
  hover?: boolean
}

export function ResponsiveCard({ children, className, hover = true }: ResponsiveCardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200',
        hover && 'hover:shadow-md hover:border-slate-300',
        className
      )}
    >
      {children}
    </div>
  )
}

interface ResponsiveTableProps {
  children: ReactNode
  className?: string
  sticky?: boolean
}

export function ResponsiveTable({ children, className, sticky = false }: ResponsiveTableProps) {
  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className={cn(
        'w-full border-collapse',
        sticky && 'sticky top-0'
      )}>
        {children}
      </table>
    </div>
  )
}
