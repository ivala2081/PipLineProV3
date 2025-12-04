import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  Activity, 
  Clock, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle,
  RefreshCw,
  BarChart3,
  X
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

interface PerformanceMonitorProps {
  enabled?: boolean;
  onPerformanceIssue?: (metrics: PerformanceMetrics) => void;
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ 
  enabled = true, 
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
  
  const [isVisible, setIsVisible] = useState(false);
  const [performanceHistory, setPerformanceHistory] = useState<PerformanceMetrics[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const apiCallTracker = useRef<{ count: number; totalTime: number; slowCount: number; errors: number }>({
    count: 0,
    totalTime: 0,
    slowCount: 0,
    errors: 0,
  });

  // Track API calls
  useEffect(() => {
    if (!enabled) return;

    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = performance.now();
      apiCallTracker.current.count++;
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        apiCallTracker.current.totalTime += duration;
        
        if (duration > 1000) { // Slow request threshold
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
  }, [enabled]);

  // Monitor performance metrics
  useEffect(() => {
    if (!enabled) return;

    const updateMetrics = () => {
      // Get memory usage
      const memoryInfo = (performance as any).memory;
      const memoryUsage = memoryInfo ? 
        Math.round((memoryInfo.usedJSHeapSize / memoryInfo.totalJSHeapSize) * 100) : 0;

      // Calculate average response time
      const averageResponseTime = apiCallTracker.current.count > 0 
        ? Math.round(apiCallTracker.current.totalTime / apiCallTracker.current.count)
        : 0;

      // Calculate cache hit rate (simplified)
      const cacheHitRate = Math.random() * 100; // Placeholder - would need actual cache tracking

      // Calculate network latency (simplified)
      const networkLatency = Math.round(Math.random() * 100); // Placeholder

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
      
      // Update history
      setPerformanceHistory(prev => {
        const updated = [...prev, newMetrics].slice(-10); // Keep last 10 measurements
        return updated;
      });

      // Check for performance issues
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

      // Reset counters
      apiCallTracker.current = { count: 0, totalTime: 0, slowCount: 0, errors: 0 };
    };

    // Update metrics every 30 seconds
    intervalRef.current = setInterval(updateMetrics, 30000);
    
    // Initial update
    updateMetrics();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, onPerformanceIssue]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  if (!enabled) return null;

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

  return (
    <div className="fixed top-4 right-4 z-50">
      <Button
        onClick={() => setIsVisible(!isVisible)}
        variant="outline"
        size="sm"
        className="shadow-lg bg-white/90 backdrop-blur-sm"
      >
        <Activity className="h-4 w-4 mr-2" />
        <span className="hidden sm:inline">Performance</span>
        <div className={`w-2 h-2 rounded-full ml-2 ${performanceStatus.color}`} />
      </Button>

      {isVisible && (
        <Card className="w-80 shadow-xl bg-white/95 backdrop-blur-sm mt-2">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm">
              <div className="flex items-center">
                <BarChart3 className="h-4 w-4 mr-2" />
                Performance Monitor
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={performanceStatus.status === 'good' ? 'default' : 'destructive'}>
                  {performanceStatus.status}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsVisible(false)}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center">
                <Database className="h-3 w-3 mr-1" />
                API Calls: {metrics.apiCallCount}
              </div>
              <div className="flex items-center">
                <Clock className="h-3 w-3 mr-1" />
                Avg Time: {metrics.averageResponseTime}ms
              </div>
              <div className="flex items-center">
                <Zap className="h-3 w-3 mr-1" />
                Slow: {metrics.slowRequests}
              </div>
              <div className="flex items-center">
                <Activity className="h-3 w-3 mr-1" />
                Memory: {metrics.memoryUsage}%
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="flex items-center justify-between text-xs">
                <span>Cache Hit Rate</span>
                <span>{metrics.cacheHitRate}%</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span>Network Latency</span>
                <span>{metrics.networkLatency}ms</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span>Errors</span>
                <span className={metrics.errors > 0 ? 'text-red-500' : 'text-green-500'}>
                  {metrics.errors}
                </span>
              </div>
            </div>

            {performanceHistory.length > 1 && (
              <div className="pt-2 border-t">
                <div className="text-xs text-gray-500 mb-1">Response Time Trend</div>
                <div className="flex items-end space-x-1 h-8">
                  {performanceHistory.slice(-8).map((m, i) => (
                    <div
                      key={i}
                      className="bg-blue-200 rounded-t"
                      style={{
                        width: '8px',
                        height: `${Math.min((m.averageResponseTime / 2000) * 100, 100)}%`,
                      }}
                      title={`${m.averageResponseTime}ms`}
                    />
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PerformanceMonitor;
