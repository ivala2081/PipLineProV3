import { useState, useRef, useEffect } from 'react'
import { Search, X, Filter } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EnhancedSearchProps {
  placeholder?: string
  onSearch: (query: string) => void
  onFilter?: () => void
  showFilter?: boolean
  className?: string
}

export function EnhancedSearch({ 
  placeholder = "Search...", 
  onSearch, 
  onFilter,
  showFilter = false,
  className 
}: EnhancedSearchProps) {
  const [query, setQuery] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(query)
    }, 300) // Debounce search

    return () => clearTimeout(timer)
  }, [query, onSearch])

  const handleClear = () => {
    setQuery('')
    inputRef.current?.focus()
  }

  return (
    <div className={cn("relative", className)}>
      <div className={cn(
        "flex items-center rounded-lg border transition-all duration-200",
        isFocused 
          ? "border-slate-400 shadow-md" 
          : "border-slate-200 hover:border-slate-300"
      )}>
        <div className="pl-3 pr-2">
          <Search className="h-4 w-4 text-slate-400" />
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className="flex-1 py-2 pr-3 text-sm placeholder:text-slate-400 focus:outline-none"
        />
        
        {query && (
          <button
            onClick={handleClear}
            className="p-1 hover:bg-slate-100 rounded"
          >
            <X className="h-4 w-4 text-slate-400" />
          </button>
        )}
        
        {showFilter && onFilter && (
          <button
            onClick={onFilter}
            className="p-2 hover:bg-slate-100 rounded-r-lg border-l border-slate-200"
          >
            <Filter className="h-4 w-4 text-slate-400" />
          </button>
        )}
      </div>
    </div>
  )
}
