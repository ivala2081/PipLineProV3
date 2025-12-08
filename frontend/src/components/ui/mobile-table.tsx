import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface MobileTableProps {
  children: ReactNode
  className?: string
}

export function MobileTable({ children, className }: MobileTableProps) {
  return (
    <div className={cn("block md:hidden", className)}>
      {children}
    </div>
  )
}

interface DesktopTableProps {
  children: ReactNode
  className?: string
}

export function DesktopTable({ children, className }: DesktopTableProps) {
  return (
    <div className={cn("hidden md:block", className)}>
      {children}
    </div>
  )
}

interface MobileCardProps {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
}

export function MobileCard({ title, subtitle, children, className }: MobileCardProps) {
  return (
    <div className={cn(
      "rounded-lg border border-slate-200 bg-white p-4 shadow-sm",
      className
    )}>
      <div className="mb-3">
        <h3 className="font-medium text-slate-900">{title}</h3>
        {subtitle && (
          <p className="text-sm text-slate-500">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  )
}
