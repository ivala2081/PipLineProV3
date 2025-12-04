import { useEffect, useRef, useCallback } from 'react';

interface PerformanceMetrics {
  renderCount: number;
  lastRenderTime: number;
  averageRenderTime: number;
  totalRenderTime: number;
}

export const usePerformanceMonitor = (componentName: string) => {
  const metricsRef = useRef<PerformanceMetrics>({
    renderCount: 0,
    lastRenderTime: 0,
    averageRenderTime: 0,
    totalRenderTime: 0
  });

  const startTimeRef = useRef<number>(0);

  // Start timing when component starts rendering
  useEffect(() => {
    startTimeRef.current = performance.now();
  });

  // Calculate render time when component finishes rendering
  useEffect(() => {
    const renderTime = performance.now() - startTimeRef.current;
    const metrics = metricsRef.current;
    
    metrics.renderCount++;
    metrics.lastRenderTime = renderTime;
    metrics.totalRenderTime += renderTime;
    metrics.averageRenderTime = metrics.totalRenderTime / metrics.renderCount;

    // Log performance data in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`🚀 ${componentName} render #${metrics.renderCount}:`, {
        renderTime: `${renderTime.toFixed(2)}ms`,
        averageTime: `${metrics.averageRenderTime.toFixed(2)}ms`,
        totalRenders: metrics.renderCount
      });
    }

    // Performance warning for slow renders
    if (renderTime > 16) { // 16ms = 60fps threshold
      console.warn(`⚠️ ${componentName} slow render: ${renderTime.toFixed(2)}ms (target: <16ms)`);
    }
  });

  const getMetrics = useCallback(() => metricsRef.current, []);

  const resetMetrics = useCallback(() => {
    metricsRef.current = {
      renderCount: 0,
      lastRenderTime: 0,
      averageRenderTime: 0,
      totalRenderTime: 0
    };
  }, []);

  return {
    getMetrics,
    resetMetrics
  };
};

export default usePerformanceMonitor;
