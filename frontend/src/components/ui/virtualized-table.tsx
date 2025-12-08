import { ReactNode, useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface VirtualizedTableProps<T> {
  data: T[]
  columns: {
    key: keyof T
    header: string
    width?: number
    render?: (value: any, row: T) => ReactNode
  }[]
  rowHeight?: number
  height?: number
  className?: string
}

export function VirtualizedTable<T>({ 
  data, 
  columns, 
  rowHeight = 40, 
  height = 400,
  className 
}: VirtualizedTableProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  const [containerHeight, setContainerHeight] = useState(height)
  const containerRef = useRef<HTMLDivElement>(null)

  const visibleStart = Math.floor(scrollTop / rowHeight)
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / rowHeight) + 1,
    data.length
  )

  const visibleData = data.slice(visibleStart, visibleEnd)
  const totalHeight = data.length * rowHeight
  const offsetY = visibleStart * rowHeight

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setContainerHeight(containerRef.current.clientHeight)
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }

  return (
    <div
      ref={containerRef}
      className={cn("overflow-auto", className)}
      style={{ height }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0
          }}
        >
          {/* Header */}
          <div className="sticky top-0 z-10 flex bg-white border-b border-slate-200">
            {columns.map((column, index) => (
              <div
                key={index}
                className="flex-1 px-4 py-3 text-left text-sm font-medium text-slate-900"
                style={{ width: column.width }}
              >
                {column.header}
              </div>
            ))}
          </div>

          {/* Rows */}
          {visibleData.map((row, index) => (
            <div
              key={visibleStart + index}
              className="flex border-b border-slate-100 hover:bg-slate-50"
              style={{ height: rowHeight }}
            >
              {columns.map((column, colIndex) => (
                <div
                  key={colIndex}
                  className="flex-1 px-4 py-3 text-sm text-slate-700"
                  style={{ width: column.width }}
                >
                  {column.render 
                    ? column.render(row[column.key], row)
                    : String(row[column.key] || '')
                  }
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
