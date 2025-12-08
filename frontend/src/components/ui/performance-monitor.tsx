import { useState, useEffect } from 'react'
import { Activity, Zap, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  networkRequests: number
  errorCount: number
}

interface PerformanceMonitorProps {
  className?: string
  showDetails?: boolean
}

export function PerformanceMonitor({ className, showDetails = false }: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    memoryUsage: 0,
    networkRequests: 0,
    errorCount: 0
  })

  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    // Monitor render performance
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry) => {
        if (entry.entryType === 'measure') {
          setMetrics(prev => ({
            ...prev,
            renderTime: entry.duration
          }))
        }
      })
    })

    observer.observe({ entryTypes: ['measure'] })

    // Monitor memory usage
    const updateMemoryUsage = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory
        setMetrics(prev => ({
          ...prev,
          memoryUsage: memory.usedJSHeapSize / 1024 / 1024 // Convert to MB
        }))
      }
    }

    updateMemoryUsage()
    const memoryInterval = setInterval(updateMemoryUsage, 5000)

    // Monitor network requests
    const originalFetch = window.fetch
    let requestCount = 0

    window.fetch = async (...args) => {
      requestCount++
      setMetrics(prev => ({
        ...prev,
        networkRequests: requestCount
      }))
      return originalFetch(...args)
    }

    // Monitor errors
    const handleError = () => {
      setMetrics(prev => ({
        ...prev,
        errorCount: prev.errorCount + 1
      }))
    }

    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleError)

    return () => {
      observer.disconnect()
      clearInterval(memoryInterval)
      window.fetch = originalFetch
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleError)
    }
  }, [])

  const getStatusColor = () => {
    if (metrics.errorCount > 0) return 'text-red-500'
    if (metrics.renderTime > 100) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getStatusIcon = () => {
    if (metrics.errorCount > 0) return <AlertTriangle className="h-4 w-4" />
    if (metrics.renderTime > 100) return <Activity className="h-4 w-4" />
    return <Zap className="h-4 w-4" />
  }

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className={cn(
          "fixed bottom-4 left-4 z-50 p-2 rounded-full bg-slate-800 text-white shadow-lg hover:bg-slate-700 transition-colors",
          className
        )}
        title="Show Performance Monitor"
      >
        <Activity className="h-4 w-4" />
      </button>
    )
  }

  return (
    <div className={cn(
      "fixed bottom-4 left-4 z-50 w-64 rounded-lg border border-slate-200 bg-white p-4 shadow-lg",
      className
    )}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="text-sm font-medium text-slate-900">Performance</span>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="text-slate-400 hover:text-slate-600"
        >
          ×
        </button>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-600">Render Time:</span>
          <span className={cn("font-mono", getStatusColor())}>
            {metrics.renderTime.toFixed(2)}ms
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-slate-600">Memory:</span>
          <span className="font-mono text-slate-900">
            {metrics.memoryUsage.toFixed(1)}MB
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-slate-600">Requests:</span>
          <span className="font-mono text-slate-900">
            {metrics.networkRequests}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-slate-600">Errors:</span>
          <span className={cn(
            "font-mono",
            metrics.errorCount > 0 ? "text-red-500" : "text-slate-900"
          )}>
            {metrics.errorCount}
          </span>
        </div>
      </div>

      {showDetails && (
        <div className="mt-3 pt-3 border-t border-slate-200">
          <div className="text-xs text-slate-500">
            <div>FPS: {Math.round(1000 / metrics.renderTime)}</div>
            <div>Load Time: {performance.timing.loadEventEnd - performance.timing.navigationStart}ms</div>
          </div>
        </div>
      )}
    </div>
  )
}
