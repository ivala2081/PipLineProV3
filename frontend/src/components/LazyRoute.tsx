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
    // #region agent log
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'LazyRoute.tsx:wrappedImportFn',message:'Starting component import',data:{importFnString:importFn.toString().substring(0,100)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B'})}).catch(()=>{});
    // #endregion
    
    // Log to console for debugging
    console.log('[LazyRoute] Starting component import...');
    
    return importFn().then((result) => {
      // #region agent log
      fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'LazyRoute.tsx:wrappedImportFn',message:'Component import succeeded',data:{hasDefault:!!result?.default,keys:result?Object.keys(result):[]},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B'})}).catch(()=>{});
      // #endregion
      
      console.log('[LazyRoute] Component import succeeded', { hasDefault: !!result?.default });
      return result;
    }).catch((error) => {
      const errorDetails = {
        message: error?.message || 'Unknown error',
        stack: error?.stack || 'No stack trace',
        name: error?.name || 'Error',
        cause: error?.cause,
        fileName: error?.fileName,
        lineNumber: error?.lineNumber,
      };
      
      // Log full error to console for debugging
      console.error('[LazyRoute] Component import failed:', errorDetails);
      console.error('[LazyRoute] Full error object:', error);
      
      // #region agent log
      fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'LazyRoute.tsx:wrappedImportFn',message:'Component import failed',data:{errorName:errorDetails.name,errorMessage:errorDetails.message,errorStack:errorDetails.stack.substring(0,500),errorCause:errorDetails.cause,errorFileName:errorDetails.fileName,errorLineNumber:errorDetails.lineNumber},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B'})}).catch(()=>{});
      // #endregion
      
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
        errorDetails.message?.includes('not found') ||
        errorDetails.message?.includes('Unexpected token') ||
        errorDetails.message?.includes('SyntaxError');
      
      // Create a user-friendly error message with more details
      let errorMessage = isChunkError
        ? `Failed to load component chunk. Error: ${errorDetails.message || 'Unknown error'}. Please try refreshing the page or clearing your cache.`
        : `Failed to load component: ${errorDetails.message || 'Unknown error'}`;
      
      const enhancedError = new Error(errorMessage);
      enhancedError.stack = errorDetails.stack;
      (enhancedError as any).originalError = error;
      (enhancedError as any).isChunkError = isChunkError;
      (enhancedError as any).errorDetails = errorDetails;
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
    
    // #region agent log
    fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'LazyRoute.tsx:render',message:'Showing error UI',data:{errorMessage:state.error.message,isChunkError,retryCount:state.retryCount},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B,C'})}).catch(()=>{});
    // #endregion
    
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
        This is usually caused by:
        <ul className="list-disc list-inside mt-2 text-left">
          <li>Network connectivity issues</li>
          <li>Outdated browser cache</li>
          <li>Missing or corrupted JavaScript files</li>
        </ul>
        Please try refreshing the page or clearing your cache.
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
            try {
              if ('caches' in window) {
                const cacheNames = await caches.keys();
                await Promise.all(cacheNames.map(name => caches.delete(name)));
              }
              if ('serviceWorker' in navigator) {
                const registrations = await navigator.serviceWorker.getRegistrations();
                await Promise.all(registrations.map(reg => reg.unregister()));
              }
              // Clear localStorage cache as well
              localStorage.clear();
              sessionStorage.clear();
              window.location.reload();
            } catch (error) {
              console.error('Error clearing cache:', error);
              window.location.reload();
            }
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
