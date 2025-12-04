import { ReactNode, useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface ContextMenuItem {
  label: string
  icon?: ReactNode
  onClick: () => void
  disabled?: boolean
  separator?: boolean
}

interface ContextMenuProps {
  children: ReactNode
  items: ContextMenuItem[]
  className?: string
}

export function ContextMenu({ children, items, className }: ContextMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const menuRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLDivElement>(null)

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    const rect = triggerRef.current?.getBoundingClientRect()
    if (rect) {
      setPosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      })
    }
    
    setIsOpen(true)
  }

  const handleClickOutside = (e: MouseEvent) => {
    if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
      setIsOpen(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
    return undefined
  }, [isOpen])

  return (
    <div
      ref={triggerRef}
      onContextMenu={handleContextMenu}
      className="relative"
    >
      {children}
      
      {isOpen && (
        <div
          ref={menuRef}
          className={cn(
            "absolute z-50 min-w-48 rounded-md border border-slate-200 bg-white py-1 shadow-lg",
            className
          )}
          style={{
            top: position.y,
            left: position.x
          }}
        >
          {items.map((item, index) => (
            <div key={index}>
              {item.separator ? (
                <div className="my-1 border-t border-slate-100" />
              ) : (
                <button
                  onClick={() => {
                    item.onClick()
                    setIsOpen(false)
                  }}
                  disabled={item.disabled}
                  className={cn(
                    "flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition-colors",
                    item.disabled
                      ? "text-slate-400 cursor-not-allowed"
                      : "text-slate-700 hover:bg-slate-100"
                  )}
                >
                  {item.icon && (
                    <span className="flex-shrink-0">
                      {item.icon}
                    </span>
                  )}
                  <span>{item.label}</span>
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
