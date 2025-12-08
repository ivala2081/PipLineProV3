import { useState, useEffect, useRef } from 'react'
import { Search, Command, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CommandItem {
  id: string
  title: string
  description?: string
  icon?: React.ReactNode
  action: () => void
  keywords?: string[]
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  items: CommandItem[]
  placeholder?: string
}

export function CommandPalette({ 
  isOpen, 
  onClose, 
  items, 
  placeholder = "Type a command or search..." 
}: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const filteredItems = items.filter(item => {
    const searchText = `${item.title} ${item.description || ''} ${item.keywords?.join(' ') || ''}`.toLowerCase()
    return searchText.includes(query.toLowerCase())
  })

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus()
      setQuery('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case 'Escape':
          onClose()
          break
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => 
            prev < filteredItems.length - 1 ? prev + 1 : 0
          )
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredItems.length - 1
          )
          break
        case 'Enter':
          e.preventDefault()
          if (filteredItems[selectedIndex]) {
            filteredItems[selectedIndex].action()
            onClose()
          }
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredItems, selectedIndex, onClose])

  useEffect(() => {
    // Scroll selected item into view
    if (listRef.current && selectedIndex >= 0) {
      const selectedElement = listRef.current.children[selectedIndex] as HTMLElement
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' })
      }
    }
  }, [selectedIndex])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-start justify-center pt-16">
      <div className="w-full max-w-2xl mx-4 bg-white rounded-lg shadow-xl">
        {/* Header */}
        <div className="flex items-center gap-3 p-4 border-b border-slate-200">
          <Search className="h-5 w-5 text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="flex-1 text-lg placeholder:text-slate-400 focus:outline-none"
          />
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-y-auto" ref={listRef}>
          {filteredItems.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <Search className="h-8 w-8 mx-auto mb-2 text-slate-300" />
              <p>No results found</p>
            </div>
          ) : (
            filteredItems.map((item, index) => (
              <button
                key={item.id}
                onClick={() => {
                  item.action()
                  onClose()
                }}
                className={cn(
                  "w-full flex items-center gap-3 p-3 text-left hover:bg-slate-50 transition-colors",
                  index === selectedIndex && "bg-slate-50"
                )}
              >
                {item.icon && (
                  <div className="flex-shrink-0 text-slate-400">
                    {item.icon}
                  </div>
                )}
                
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900">{item.title}</p>
                  {item.description && (
                    <p className="text-sm text-slate-500">{item.description}</p>
                  )}
                </div>
                
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-200 text-xs text-slate-500">
          <div className="flex items-center justify-between">
            <span>Use ↑↓ to navigate, Enter to select, Esc to close</span>
            <span>{filteredItems.length} result{filteredItems.length !== 1 ? 's' : ''}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
