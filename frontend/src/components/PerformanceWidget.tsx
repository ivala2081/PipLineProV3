import React, { useState, useEffect, useRef } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  Activity, 
  Clock, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle,
  BarChart3,
  X,
  Settings
} from 'lucide-react';

interface PerformanceMetrics {
  apiCallCount: number;
  averageResponseTime: number;
  slowRequests: number;
  cacheHitRate: number;
  memoryUsage: number;
  networkLatency: number;
  errors: number;
}

interface PerformanceWidgetProps {
  position?: 'header' | 'floating' | 'sidebar';
  compact?: boolean;
  onPerformanceIssue?: (metrics: PerformanceMetrics) => void;
}

export const PerformanceWidget: React.FC<PerformanceWidgetProps> = ({ 
  position = 'header',
  compact = true,
  onPerformanceIssue 
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    apiCallCount: 0,
    averageResponseTime: 0,
    slowRequests: 0,
    cacheHitRate: 0,
    memoryUsage: 0,
    networkLatency: 0,
    errors: 0,
  });
  
  const [isExpanded, setIsExpanded] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const apiCallTracker = useRef<{ count: number; totalTime: number; slowCount: number; errors: number }>({
    count: 0,
    totalTime: 0,
    slowCount: 0,
    errors: 0,
  });

  // Track API calls (same logic as PerformanceMonitor)
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();
      apiCallTracker.current.count++;
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        apiCallTracker.current.totalTime += duration;
        
        if (duration > 1000) {
          apiCallTracker.current.slowCount++;
        }
        
        return response;
      } catch (error) {
        apiCallTracker.current.errors++;
        throw error;
      }
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  // Monitor performance metrics
  useEffect(() => {
    const updateMetrics = () => {
      const memoryInfo = (performance as any).memory;
      const memoryUsage = memoryInfo ? 
        Math.round((memoryInfo.usedJSHeapSize / memoryInfo.totalJSHeapSize) * 100) : 0;

      const averageResponseTime = apiCallTracker.current.count > 0 
        ? Math.round(apiCallTracker.current.totalTime / apiCallTracker.current.count)
        : 0;

      const cacheHitRate = Math.random() * 100;
      const networkLatency = Math.round(Math.random() * 100);

      const newMetrics: PerformanceMetrics = {
        apiCallCount: apiCallTracker.current.count,
        averageResponseTime,
        slowRequests: apiCallTracker.current.slowCount,
        cacheHitRate: Math.round(cacheHitRate),
        memoryUsage,
        networkLatency,
        errors: apiCallTracker.current.errors,
      };

      setMetrics(newMetrics);

      if (onPerformanceIssue) {
        const hasIssues = 
          newMetrics.averageResponseTime > 2000 ||
          newMetrics.slowRequests > 5 ||
          newMetrics.memoryUsage > 80 ||
          newMetrics.errors > 3;
        
        if (hasIssues) {
          onPerformanceIssue(newMetrics);
        }
      }

      apiCallTracker.current = { count: 0, totalTime: 0, slowCount: 0, errors: 0 };
    };

    intervalRef.current = setInterval(updateMetrics, 30000);
    updateMetrics();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [onPerformanceIssue]);

  const getPerformanceStatus = () => {
    if (metrics.averageResponseTime > 2000 || metrics.slowRequests > 5) {
      return { status: 'poor', color: 'bg-red-500', icon: AlertTriangle };
    } else if (metrics.averageResponseTime > 1000 || metrics.slowRequests > 2) {
      return { status: 'fair', color: 'bg-yellow-500', icon: Clock };
    } else {
      return { status: 'good', color: 'bg-green-500', icon: CheckCircle };
    }
  };

  const performanceStatus = getPerformanceStatus();

  // Compact header version
  if (position === 'header' && compact) {
    return (
      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1 text-xs text-gray-600">
          <Database className="h-3 w-3" />
          <span>{metrics.apiCallCount}</span>
        </div>
        <div className="flex items-center space-x-1 text-xs text-gray-600">
          <Clock className="h-3 w-3" />
          <span>{metrics.averageResponseTime}ms</span>
        </div>
        <div className={`w-2 h-2 rounded-full ${performanceStatus.color}`} 
             title={`Performance: ${performanceStatus.status}`} />
      </div>
    );
  }

  // Floating version
  if (position === 'floating') {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <div className="flex flex-col space-y-2">
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            variant="outline"
            size="sm"
            className="shadow-lg bg-white/90 backdrop-blur-sm"
          >
            <Activity className="h-4 w-4 mr-2" />
            Perf
            <div className={`w-2 h-2 rounded-full ml-2 ${performanceStatus.color}`} />
          </Button>

          {isExpanded && (
            <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-xl p-3 w-64">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Performance</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsExpanded(false)}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center">
                  <Database className="h-3 w-3 mr-1" />
                  {metrics.apiCallCount} calls
                </div>
                <div className="flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {metrics.averageResponseTime}ms
                </div>
                <div className="flex items-center">
                  <Zap className="h-3 w-3 mr-1" />
                  {metrics.slowRequests} slow
                </div>
                <div className="flex items-center">
                  <Activity className="h-3 w-3 mr-1" />
                  {metrics.memoryUsage}% mem
                </div>
              </div>
              
              <div className="mt-2 pt-2 border-t">
                <Badge variant={performanceStatus.status === 'good' ? 'default' : 'destructive'} className="text-xs">
                  {performanceStatus.status}
                </Badge>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Sidebar version
  if (position === 'sidebar') {
    return (
      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-600">Performance</span>
          <div className={`w-2 h-2 rounded-full ${performanceStatus.color}`} />
        </div>
        
        <div className="space-y-1 text-xs text-gray-500">
          <div className="flex justify-between">
            <span>API Calls:</span>
            <span>{metrics.apiCallCount}</span>
          </div>
          <div className="flex justify-between">
            <span>Avg Time:</span>
            <span>{metrics.averageResponseTime}ms</span>
          </div>
          <div className="flex justify-between">
            <span>Memory:</span>
            <span>{metrics.memoryUsage}%</span>
          </div>
          <div className="flex justify-between">
            <span>Errors:</span>
            <span className={metrics.errors > 0 ? 'text-red-500' : 'text-green-500'}>
              {metrics.errors}
            </span>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default PerformanceWidget;
