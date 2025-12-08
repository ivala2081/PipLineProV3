import { ReactNode, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FloatingActionProps {
  onClick: () => void
  icon?: ReactNode
  label?: string
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  className?: string
}

export function FloatingAction({ 
  onClick, 
  icon = <Plus className="h-5 w-5" />, 
  label,
  position = 'bottom-right',
  className 
}: FloatingActionProps) {
  const [isHovered, setIsHovered] = useState(false)

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6'
  }

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "fixed z-50 flex items-center gap-2 rounded-full bg-slate-800 text-white shadow-lg transition-all duration-200 hover:bg-slate-700 hover:shadow-xl",
        positionClasses[position],
        className
      )}
    >
      <div className="p-3">
        {icon}
      </div>
      {label && (
        <div className={cn(
          "pr-4 transition-all duration-200 overflow-hidden",
          isHovered ? "max-w-32 opacity-100" : "max-w-0 opacity-0"
        )}>
          <span className="text-sm font-medium whitespace-nowrap">
            {label}
          </span>
        </div>
      )}
    </button>
  )
}

interface FloatingMenuProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
}

export function FloatingMenu({ 
  isOpen, 
  onClose, 
  children, 
  position = 'bottom-right' 
}: FloatingMenuProps) {
  if (!isOpen) return null

  const positionClasses = {
    'bottom-right': 'bottom-20 right-6',
    'bottom-left': 'bottom-20 left-6',
    'top-right': 'top-20 right-6',
    'top-left': 'top-20 left-6'
  }

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-40 bg-black/20"
        onClick={onClose}
      />
      
      {/* Menu */}
      <div className={cn(
        "fixed z-50 min-w-48 rounded-lg border border-slate-200 bg-white shadow-xl",
        positionClasses[position]
      )}>
        <div className="p-2">
          {children}
        </div>
      </div>
    </>
  )
}
