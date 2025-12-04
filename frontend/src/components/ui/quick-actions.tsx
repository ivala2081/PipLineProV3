import { ReactNode, useState } from 'react'
import { Plus, Search, Filter, Download, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface QuickAction {
  id: string
  label: string
  icon: ReactNode
  action: () => void
  shortcut?: string
  variant?: 'primary' | 'secondary' | 'outline'
}

interface QuickActionsProps {
  actions: QuickAction[]
  className?: string
}

export function QuickActions({ actions, className }: QuickActionsProps) {
  const [activeAction, setActiveAction] = useState<string | null>(null)

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {actions.map((action) => (
        <button
          key={action.id}
          onClick={() => {
            action.action()
            setActiveAction(action.id)
            setTimeout(() => setActiveAction(null), 200)
          }}
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
            "hover:scale-105 active:scale-95",
            action.variant === 'primary' 
              ? "bg-slate-800 text-white hover:bg-slate-700 shadow-md"
              : action.variant === 'outline'
              ? "border border-slate-200 text-slate-700 hover:bg-slate-50"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200",
            activeAction === action.id && "scale-95"
          )}
          title={action.shortcut ? `${action.label} (${action.shortcut})` : action.label}
        >
          {action.icon}
          <span>{action.label}</span>
          {action.shortcut && (
            <span className="ml-1 text-xs opacity-60">
              {action.shortcut}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}

// Common quick actions
export const commonQuickActions: QuickAction[] = [
  {
    id: 'add',
    label: 'Add New',
    icon: <Plus className="h-4 w-4" />,
    action: () => console.log('Add new item'),
    shortcut: 'Ctrl+N',
    variant: 'primary'
  },
  {
    id: 'search',
    label: 'Search',
    icon: <Search className="h-4 w-4" />,
    action: () => console.log('Open search'),
    shortcut: 'Ctrl+K',
    variant: 'secondary'
  },
  {
    id: 'filter',
    label: 'Filter',
    icon: <Filter className="h-4 w-4" />,
    action: () => console.log('Open filters'),
    variant: 'outline'
  },
  {
    id: 'export',
    label: 'Export',
    icon: <Download className="h-4 w-4" />,
    action: () => console.log('Export data'),
    shortcut: 'Ctrl+E',
    variant: 'outline'
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <Settings className="h-4 w-4" />,
    action: () => console.log('Open settings'),
    variant: 'outline'
  }
]
