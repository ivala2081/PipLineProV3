/**
 * Resource Hints Manager
 * Dynamically adds preload, prefetch, and preconnect hints for performance
 */

interface ResourceHint {
  href: string;
  as?: string;
  type?: string;
  crossorigin?: boolean;
}

class ResourceHintsManager {
  private preloadedResources: Set<string> = new Set();
  private prefetchedResources: Set<string> = new Set();

  /**
   * Preload a critical resource
   */
  preload(href: string, as: string, type?: string, crossorigin?: boolean): void {
    if (this.preloadedResources.has(href)) {
      return;
    }

    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = href;
    link.as = as;
    if (type) link.type = type;
    if (crossorigin) link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
    this.preloadedResources.add(href);
  }

  /**
   * Prefetch a resource for future navigation
   */
  prefetch(href: string): void {
    if (this.prefetchedResources.has(href)) {
      return;
    }

    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.appendChild(link);
    this.prefetchedResources.add(href);
  }

  /**
   * Preconnect to an origin
   */
  preconnect(href: string, crossorigin?: boolean): void {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = href;
    if (crossorigin) link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  }

  /**
   * DNS prefetch to an origin
   */
  dnsPrefetch(href: string): void {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = href;
    document.head.appendChild(link);
  }

  /**
   * Prefetch route chunks for next navigation
   */
  prefetchRoute(routePath: string): void {
    // This would be implemented based on your build output
    // For Vite, you'd need to know the chunk names
    console.log(`Prefetching route: ${routePath}`);
  }

  /**
   * Preload critical images
   */
  preloadImage(src: string, srcset?: string, sizes?: string): void {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = src;
    if (srcset) link.setAttribute('imagesrcset', srcset);
    if (sizes) link.setAttribute('imagesizes', sizes);
    document.head.appendChild(link);
    this.preloadedResources.add(src);
  }

  /**
   * Prefetch fonts
   */
  prefetchFont(href: string, type: string = 'font/woff2'): void {
    this.preload(href, 'font', type, true);
  }
}

export const resourceHints = new ResourceHintsManager();
export default resourceHints;

