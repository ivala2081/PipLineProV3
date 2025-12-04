/**
 * LazyRoute component for route-based lazy loading with enhanced features
 */

import React, { Suspense, lazy, ComponentType } from 'react';
import { useLazyLoading } from '../hooks/useLazyLoading';
import LoadingSpinner from './LoadingSpinner';
import EnhancedErrorBoundary from './EnhancedErrorBoundary';

interface LazyRouteProps {
  importFn: () => Promise<{ default: ComponentType<any> }>;
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
  preload?: boolean;
  preloadDelay?: number;
  retryCount?: number;
  retryDelay?: number;
  [key: string]: any;
}

const LazyRoute: React.FC<LazyRouteProps> = ({
  importFn,
  fallback = <LoadingSpinner />,
  errorFallback = (
    <div className="flex items-center justify-center min-h-[200px] p-8">
      <div className="text-center">
        <div className="text-red-500 text-lg font-semibold mb-2">
          Failed to load component
        </div>
        <div className="text-gray-600 text-sm">
          Please try refreshing the page or contact support if the problem persists.
        </div>
      </div>
    </div>
  ),
  preload = true,
  preloadDelay = 1000,
  retryCount = 3,
  retryDelay = 2000,
  ...props
}) => {
  const { state, preload: preloadComponent, retry } = useLazyLoading(importFn, {
    preload,
    preloadDelay,
    cache: true,
    retryCount,
    retryDelay,
  });

  const LazyComponent = lazy(importFn);

  // Enhanced fallback with retry option
  const enhancedFallback = state.error ? (
    <div className="flex items-center justify-center min-h-[200px] p-8">
      <div className="text-center">
        <div className="text-red-500 text-lg font-semibold mb-2">
          Failed to load component
        </div>
        <div className="text-gray-600 text-sm mb-4">
          {state.error.message}
        </div>
        <button
          onClick={retry}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  ) : fallback;

  return (
    <EnhancedErrorBoundary fallback={errorFallback}>
      <Suspense fallback={enhancedFallback}>
        <LazyComponent {...props} />
      </Suspense>
    </EnhancedErrorBoundary>
  );
};

// Higher-order component for creating lazy routes
export const createLazyRoute = (
  importFn: () => Promise<{ default: ComponentType<any> }>,
  options: Partial<LazyRouteProps> = {}
) => {
  return (props: any) => (
    <LazyRoute
      importFn={importFn}
      {...options}
      {...props}
    />
  );
};

// Predefined lazy route configurations
export const LazyRouteConfigs = {
  // Critical components (preload immediately)
  critical: {
    preload: true,
    preloadDelay: 0,
    retryCount: 5,
    retryDelay: 1000,
  },
  
  // Standard components (preload after 1 second)
  standard: {
    preload: true,
    preloadDelay: 1000,
    retryCount: 3,
    retryDelay: 2000,
  },
  
  // Heavy components (preload after 2 seconds)
  heavy: {
    preload: true,
    preloadDelay: 2000,
    retryCount: 2,
    retryDelay: 3000,
  },
  
  // On-demand components (no preload)
  onDemand: {
    preload: false,
    retryCount: 3,
    retryDelay: 2000,
  },
};

export default LazyRoute;
