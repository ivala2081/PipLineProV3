/**
 * Lazy-loaded components for better performance
 * These components are only loaded when needed
 */

import React, { Suspense, lazy } from 'react';
import LoadingSpinner from './LoadingSpinner';
import { lazyLoadingOptimizer } from '../utils/lazyLoadingOptimizer';

// Lazy load heavy components
export const LazyDashboard = lazy(() => import('./modern/ModernDashboard'));
export const LazyRevenueChart = lazy(() => import('./modern/RevenueChart'));
export const LazyDataTable = lazy(() => import('./modern/DataTable'));
export const LazyGlobalSearch = lazy(() => import('./modern/GlobalSearch'));
export const LazyModernHeader = lazy(() => import('./modern/ModernHeader').then(module => ({ default: module.ModernHeader })));
export const LazyModernLayout = lazy(() => import('./modern/ModernLayout'));
export const LazyNotificationSystem = lazy(() => import('./modern/NotificationSystem').then(module => ({ default: module.NotificationSystem })));
export const LazyProgressIndicator = lazy(() => import('./modern/ProgressIndicator').then(module => ({ default: module.ProgressIndicator })));
export const LazySkeletonLoader = lazy(() => import('./modern/SkeletonLoader').then(module => ({ default: module.SkeletonLoader })));

// Lazy load forms and modals (only if they exist)
// export const LazyTransactionForm = lazy(() => import('./forms/TransactionForm'));
// export const LazyClientForm = lazy(() => import('./forms/ClientForm'));
// export const LazyPSPForm = lazy(() => import('./forms/PSPForm'));
// export const LazySettingsModal = lazy(() => import('./modals/SettingsModal'));

// Lazy load admin components (only if they exist)
// export const LazyUserManagement = lazy(() => import('./admin/UserManagement'));
// export const LazySystemSettings = lazy(() => import('./admin/SystemSettings'));
// export const LazyAuditLog = lazy(() => import('./admin/AuditLog'));

// Higher-order component for lazy loading with fallback
export const withLazyLoading = <P extends Record<string, any>>(
  Component: React.ComponentType<P>,
  fallback?: React.ReactNode
) => {
  const LazyComponent = lazy(() => Promise.resolve({ default: Component }));
  
  return (props: P) => (
    <Suspense fallback={fallback || <LoadingSpinner />}>
      <LazyComponent {...(props as any)} />
    </Suspense>
  );
};

// Preload components for better UX
export const preloadComponents = async () => {
  const startTime = performance.now();
  
  try {
    // Preload critical components
    await Promise.all([
      import('./modern/ModernDashboard'),
      import('./modern/ModernHeader'),
      import('./modern/ModernLayout'),
    ]);
    
    // Preload existing charts and data components
    await Promise.all([
      import('./modern/RevenueChart'),
      import('./modern/DataTable'),
      import('./modern/GlobalSearch'),
    ]);
    
    // Preload UI components
    await Promise.all([
      import('./modern/NotificationSystem'),
      import('./modern/ProgressIndicator'),
      import('./modern/SkeletonLoader'),
    ]);

    const loadTime = performance.now() - startTime;
    lazyLoadingOptimizer.recordMetrics('preloadComponents', {
      loadTime,
      preloadSuccess: true,
      cacheHit: false,
      retryCount: 0,
      errorRate: 0,
    });

    console.log(`Components preloaded successfully in ${loadTime.toFixed(2)}ms`);
  } catch (error) {
    const loadTime = performance.now() - startTime;
    lazyLoadingOptimizer.recordMetrics('preloadComponents', {
      loadTime,
      preloadSuccess: false,
      cacheHit: false,
      retryCount: 0,
      errorRate: 1,
    });
    
    console.error('Failed to preload components:', error);
  }
};

// Component that handles lazy loading with error boundaries
interface LazyComponentProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
}

export const LazyWrapper: React.FC<LazyComponentProps> = ({
  children,
  fallback = <LoadingSpinner />,
  errorFallback = <div className="text-center p-4 text-red-500">Failed to load component</div>
}) => {
  return (
    <Suspense fallback={fallback}>
      <ErrorBoundary fallback={errorFallback}>
        {children}
      </ErrorBoundary>
    </Suspense>
  );
};

// Error boundary for lazy components
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  override componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Lazy component error:', error, errorInfo);
  }

  override render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

// Hook for preloading components
export const usePreload = () => {
  const preload = React.useCallback((component: () => Promise<any>) => {
    component();
  }, []);

  return { preload };
};

// Export all lazy components
export default {
  LazyDashboard,
  LazyRevenueChart,
  LazyDataTable,
  LazyGlobalSearch,
  LazyModernHeader,
  LazyModernLayout,
  LazyNotificationSystem,
  LazyProgressIndicator,
  LazySkeletonLoader,
  withLazyLoading,
  preloadComponents,
  LazyWrapper
};
