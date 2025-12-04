import { useState, ReactNode } from 'react'
import { Trash2, Edit, Download, MoreHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BulkAction {
  id: string
  label: string
  icon: ReactNode
  action: () => void
  variant?: 'default' | 'destructive' | 'outline'
}

interface BulkActionsProps {
  selectedCount: number
  totalCount: number
  actions: BulkAction[]
  onSelectAll: () => void
  onClearSelection: () => void
  className?: string
}

export function BulkActions({ 
  selectedCount, 
  totalCount, 
  actions, 
  onSelectAll, 
  onClearSelection,
  className 
}: BulkActionsProps) {
  const [showActions, setShowActions] = useState(false)

  if (selectedCount === 0) return null

  return (
    <div className={cn(
      "fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50",
      "bg-white rounded-lg border border-slate-200 shadow-lg p-4",
      className
    )}>
      <div className="flex items-center gap-4">
        {/* Selection Info */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-slate-900">
            {selectedCount} selected
          </span>
          <button
            onClick={onSelectAll}
            className="text-sm text-slate-600 hover:text-slate-900 underline"
          >
            Select all {totalCount}
          </button>
          <button
            onClick={onClearSelection}
            className="text-sm text-slate-600 hover:text-slate-900 underline"
          >
            Clear
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {actions.slice(0, 3).map((action) => (
            <button
              key={action.id}
              onClick={action.action}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                action.variant === 'destructive' 
                  ? "bg-red-50 text-red-700 hover:bg-red-100"
                  : action.variant === 'outline'
                  ? "border border-slate-200 text-slate-700 hover:bg-slate-50"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              )}
            >
              {action.icon}
              {action.label}
            </button>
          ))}

          {actions.length > 3 && (
            <div className="relative">
              <button
                onClick={() => setShowActions(!showActions)}
                className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <MoreHorizontal className="h-4 w-4" />
                More
              </button>

              {showActions && (
                <div className="absolute bottom-full right-0 mb-2 w-48 rounded-md border border-slate-200 bg-white shadow-lg">
                  <div className="p-1">
                    {actions.slice(3).map((action) => (
                      <button
                        key={action.id}
                        onClick={() => {
                          action.action()
                          setShowActions(false)
                        }}
                        className={cn(
                          "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm text-left transition-colors",
                          action.variant === 'destructive' 
                            ? "text-red-700 hover:bg-red-50"
                            : "text-slate-700 hover:bg-slate-50"
                        )}
                      >
                        {action.icon}
                        {action.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Common bulk actions
export const commonBulkActions: BulkAction[] = [
  {
    id: 'edit',
    label: 'Edit',
    icon: <Edit className="h-4 w-4" />,
    action: () => console.log('Edit selected items'),
    variant: 'default'
  },
  {
    id: 'export',
    label: 'Export',
    icon: <Download className="h-4 w-4" />,
    action: () => console.log('Export selected items'),
    variant: 'outline'
  },
  {
    id: 'delete',
    label: 'Delete',
    icon: <Trash2 className="h-4 w-4" />,
    action: () => console.log('Delete selected items'),
    variant: 'destructive'
  }
]
