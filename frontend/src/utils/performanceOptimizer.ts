/**
 * Performance Optimizer
 * Bundle size, lazy loading, and runtime performance optimizations
 */

import { logger } from './logger';

class PerformanceOptimizer {
  private imageObserver: IntersectionObserver | null = null;
  private lazyImages: Set<HTMLImageElement> = new Set();

  /**
   * Setup lazy loading for images
   */
  setupLazyImages(): void {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      return;
    }

    this.imageObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            const src = img.dataset.src;
            if (src) {
              img.src = src;
              img.removeAttribute('data-src');
              this.imageObserver?.unobserve(img);
              this.lazyImages.delete(img);
            }
          }
        });
      },
      {
        rootMargin: '50px',
      },
    );

    // Observe all images with data-src attribute
    document.querySelectorAll('img[data-src]').forEach((img) => {
      this.lazyImages.add(img as HTMLImageElement);
      this.imageObserver?.observe(img);
    });
  }

  /**
   * Preload critical resources
   */
  preloadResource(href: string, as: string): void {
    if (typeof document === 'undefined') return;

    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = href;
    link.as = as;
    document.head.appendChild(link);
  }

  /**
   * Prefetch resources for next navigation
   */
  prefetchResource(href: string): void {
    if (typeof document === 'undefined') return;

    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.appendChild(link);
  }

  /**
   * Debounce function for performance
   */
  debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout | null = null;

    return function executedFunction(...args: Parameters<T>) {
      const later = () => {
        timeout = null;
        func(...args);
      };

      if (timeout) {
        clearTimeout(timeout);
      }
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Throttle function for performance
   */
  throttle<T extends (...args: any[]) => any>(func: T, limit: number): (...args: Parameters<T>) => void {
    let inThrottle: boolean;

    return function executedFunction(...args: Parameters<T>) {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  /**
   * Measure performance
   */
  measurePerformance(name: string, fn: () => void): void {
    if (typeof performance === 'undefined') {
      fn();
      return;
    }

    const start = performance.now();
    fn();
    const end = performance.now();
    const duration = end - start;

    logger.performance(name, duration);

    // Warn if operation takes too long
    if (duration > 100) {
      logger.warn(`Slow operation detected: ${name} took ${duration.toFixed(2)}ms`);
    }
  }

  /**
   * Cleanup
   */
  cleanup(): void {
    if (this.imageObserver) {
      this.lazyImages.forEach((img) => {
        this.imageObserver?.unobserve(img);
      });
      this.lazyImages.clear();
      this.imageObserver.disconnect();
      this.imageObserver = null;
    }
  }
}

// Export singleton instance
export const performanceOptimizer = new PerformanceOptimizer();
export default performanceOptimizer;
