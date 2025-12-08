import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface ProgressIndicatorProps {
  steps: {
    id: string
    label: string
    status: 'completed' | 'current' | 'upcoming'
    description?: string
  }[]
  className?: string
}

export function ProgressIndicator({ steps, className }: ProgressIndicatorProps) {
  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            {/* Step Circle */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-medium transition-colors",
                  step.status === 'completed' && "border-emerald-500 bg-emerald-500 text-white",
                  step.status === 'current' && "border-slate-500 bg-slate-500 text-white",
                  step.status === 'upcoming' && "border-slate-300 bg-white text-slate-400"
                )}
              >
                {step.status === 'completed' ? (
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              
              {/* Step Label */}
              <div className="mt-2 text-center">
                <p className={cn(
                  "text-sm font-medium",
                  step.status === 'completed' && "text-emerald-600",
                  step.status === 'current' && "text-slate-900",
                  step.status === 'upcoming' && "text-slate-400"
                )}>
                  {step.label}
                </p>
                {step.description && (
                  <p className="text-xs text-slate-500 mt-1">
                    {step.description}
                  </p>
                )}
              </div>
            </div>
            
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "h-0.5 w-16 mx-4 transition-colors",
                  step.status === 'completed' ? "bg-emerald-500" : "bg-slate-300"
                )}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
