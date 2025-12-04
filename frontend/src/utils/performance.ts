// Performance monitoring utility
interface PerformanceMetric {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map();
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  private initializeObservers() {
    // Monitor navigation timing
    if ('PerformanceObserver' in window) {
      try {
        const navigationObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.entryType === 'navigation') {
              const navEntry = entry as PerformanceNavigationTiming;
              this.logNavigationMetrics(navEntry);
            }
          });
        });
        navigationObserver.observe({ entryTypes: ['navigation'] });
        this.observers.push(navigationObserver);
      } catch (error) {
        console.warn('Navigation performance observer not supported:', error);
      }

      // Monitor resource loading
      try {
        const resourceObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.entryType === 'resource') {
              const resourceEntry = entry as PerformanceResourceTiming;
              this.logResourceMetrics(resourceEntry);
            }
          });
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (error) {
        console.warn('Resource performance observer not supported:', error);
      }
    }
  }

  startTimer(name: string, metadata?: Record<string, any>): void {
    this.metrics.set(name, {
      name,
      startTime: performance.now(),
      metadata,
    });
  }

  endTimer(name: string): number | null {
    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`Performance timer '${name}' not found`);
      return null;
    }

    metric.endTime = performance.now();
    metric.duration = metric.endTime - metric.startTime;

    this.logMetric(metric);
    this.metrics.delete(name);
    return metric.duration;
  }

  measureAsync<T>(name: string, asyncFn: () => Promise<T>, metadata?: Record<string, any>): Promise<T> {
    this.startTimer(name, metadata);
    return asyncFn().finally(() => {
      this.endTimer(name);
    });
  }

  private logMetric(metric: PerformanceMetric): void {
    if (process.env.NODE_ENV === 'development') {
      console.log(`⏱️ Performance: ${metric.name}`, {
        duration: `${metric.duration?.toFixed(2)}ms`,
        metadata: metric.metadata,
      });
    }

    // Send to analytics in production
    if (process.env.NODE_ENV === 'production' && metric.duration && metric.duration > 1000) {
      this.reportSlowOperation(metric);
    }
  }

  private logNavigationMetrics(navEntry: PerformanceNavigationTiming): void {
    const metrics = {
      'DNS Lookup': navEntry.domainLookupEnd - navEntry.domainLookupStart,
      'TCP Connection': navEntry.connectEnd - navEntry.connectStart,
      'Server Response': navEntry.responseEnd - navEntry.requestStart,
      'DOM Content Loaded': navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
      'Page Load': navEntry.loadEventEnd - navEntry.loadEventStart,
      'Total Time': navEntry.loadEventEnd - navEntry.fetchStart,
    };

    if (process.env.NODE_ENV === 'development') {
      console.log('🌐 Navigation Performance:', metrics);
    }
  }

  private logResourceMetrics(resourceEntry: PerformanceResourceTiming): void {
    const duration = resourceEntry.responseEnd - resourceEntry.fetchStart;
    
    // Only log slow resources
    if (duration > 1000) {
      if (process.env.NODE_ENV === 'development') {
        console.log('🐌 Slow Resource:', {
          name: resourceEntry.name,
          duration: `${duration.toFixed(2)}ms`,
          size: resourceEntry.transferSize,
        });
      }
    }
  }

  private reportSlowOperation(metric: PerformanceMetric): void {
    // In production, you would send this to your analytics service
    // For now, we'll just log it
    console.warn('🐌 Slow operation detected:', {
      name: metric.name,
      duration: metric.duration,
      metadata: metric.metadata,
    });
  }

  getMetrics(): PerformanceMetric[] {
    return Array.from(this.metrics.values());
  }

  clearMetrics(): void {
    this.metrics.clear();
  }

  disconnect(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Convenience functions
export const startTimer = (name: string, metadata?: Record<string, any>) => 
  performanceMonitor.startTimer(name, metadata);

export const endTimer = (name: string) => 
  performanceMonitor.endTimer(name);

export const measureAsync = <T>(name: string, asyncFn: () => Promise<T>, metadata?: Record<string, any>) => 
  performanceMonitor.measureAsync(name, asyncFn, metadata);

export default performanceMonitor;
