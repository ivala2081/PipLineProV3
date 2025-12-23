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
  errorFallback,
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

  // Wrap import function to catch errors
  const wrappedImportFn = () => {
    return importFn().catch((error) => {
      const errorDetails = {
        message: error?.message || 'Unknown error',
        stack: error?.stack || 'No stack trace',
        name: error?.name || 'Error',
      };
      
      // Check if it's a chunk loading error (common in production)
      const isChunkError = 
        errorDetails.message?.includes('Failed to fetch') ||
        errorDetails.message?.includes('Loading chunk') ||
        errorDetails.message?.includes('Loading CSS chunk') ||
        errorDetails.message?.includes('ChunkLoadError') ||
        errorDetails.name === 'ChunkLoadError' ||
        errorDetails.message?.includes('network error') ||
        errorDetails.message?.includes('Failed to fetch dynamically imported module') ||
        errorDetails.message?.includes('404') ||
        errorDetails.message?.includes('not found');
      
      // Create a user-friendly error message
      let errorMessage = isChunkError
        ? 'Failed to load component. Please refresh the page.'
        : `Failed to load component: ${errorDetails.message}`;
      
      const enhancedError = new Error(errorMessage);
      enhancedError.stack = errorDetails.stack;
      (enhancedError as any).originalError = error;
      (enhancedError as any).isChunkError = isChunkError;
      throw enhancedError;
    });
  };
  
  const LazyComponent = lazy(wrappedImportFn);

  // Enhanced fallback with retry option
  const enhancedFallback = state.error ? (
    <div className="flex items-center justify-center min-h-[200px] p-8">
      <div className="text-center max-w-md">
        <div className="text-red-500 text-lg font-semibold mb-2">
          Failed to load component
        </div>
        <div className="text-gray-600 text-sm mb-4">
          {state.error.message || 'An error occurred while loading the component'}
        </div>
        {state.error.stack && (
          <details className="text-left text-xs text-gray-500 mb-4 bg-gray-50 p-2 rounded">
            <summary className="cursor-pointer mb-2">Error Details</summary>
            <pre className="whitespace-pre-wrap overflow-auto max-h-40">
              {state.error.stack}
            </pre>
          </details>
        )}
        <button
          onClick={retry}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Retry
        </button>
      </div>
    </div>
  ) : fallback;

  // If there's an error in the loading state, show error immediately
  if (state.error) {
    const isChunkError = (state.error as any)?.isChunkError || false;
    
    return (
      <div className="flex items-center justify-center min-h-[200px] p-8">
        <div className="text-center max-w-lg">
          <div className="text-red-500 text-lg font-semibold mb-2">
            Failed to load component
          </div>
          <div className="text-gray-600 text-sm mb-4">
            {isChunkError 
              ? 'The page could not be loaded. Please refresh.'
              : (state.error.message || 'An error occurred while loading the component')}
          </div>
          
          <div className="flex gap-2 justify-center flex-wrap">
            <button
              onClick={retry}
              className="px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors"
            >
              Retry
            </button>
            <button
              onClick={async () => {
                if ('serviceWorker' in navigator) {
                  try {
                    const registrations = await navigator.serviceWorker.getRegistrations();
                    for (const registration of registrations) {
                      await registration.unregister();
                    }
                    if ('caches' in window) {
                      const cacheNames = await caches.keys();
                      await Promise.all(cacheNames.map(name => caches.delete(name)));
                    }
                  } catch (e) {
                    // Silently fail
                  }
                }
                window.location.reload();
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Clear Cache & Reload
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Default error fallback
  const defaultErrorFallback = (
    <div className="flex items-center justify-center min-h-[200px] p-8">
      <div className="text-center max-w-md">
        <div className="text-red-500 text-lg font-semibold mb-2">
          Failed to load component
        </div>
        <div className="text-gray-600 text-sm mb-4">
          Please try refreshing the page or contact support if the problem persists.
        </div>
        <div className="flex gap-2 justify-center">
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors"
          >
            Refresh Page
          </button>
          <button
            onClick={async () => {
              if ('caches' in window) {
                const cacheNames = await caches.keys();
                await Promise.all(cacheNames.map(name => caches.delete(name)));
              }
              if ('serviceWorker' in navigator) {
                const registrations = await navigator.serviceWorker.getRegistrations();
                await Promise.all(registrations.map(reg => reg.unregister()));
              }
              window.location.reload();
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Clear Cache & Reload
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <EnhancedErrorBoundary fallback={errorFallback || defaultErrorFallback}>
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
