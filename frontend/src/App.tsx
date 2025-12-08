import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy, useEffect } from 'react';
import { SWRConfig } from 'swr';
import { Provider } from 'react-redux';
import { store } from './store';
import Layout from './components/modern/ModernLayout';
import LoadingSpinner from './components/LoadingSpinner';
import ProtectedRoute from './components/ProtectedRoute';
import EnhancedErrorBoundary from './components/EnhancedErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';
import { LanguageProvider } from './contexts/LanguageContext';
import { AccessibilityProvider } from './contexts/AccessibilityContext';
import { NavigationProvider } from './contexts/NavigationContext';
import { swrConfig } from './config/swrConfig';
import { NotificationProvider } from './contexts/NotificationContext';
import SkipLink from './components/SkipLink';
import PerformanceWidget from './components/PerformanceWidget';
import NavigationLoadingIndicator from './components/NavigationLoadingIndicator';
import { useScrollRestoration } from './hooks/useScrollRestoration';
import { preloadComponents } from './components/LazyComponents';
import { performanceOptimizer } from './utils/performanceOptimizer';
import LazyRoute, { createLazyRoute, LazyRouteConfigs } from './components/LazyRoute';
import { lazyLoadingOptimizer } from './utils/lazyLoadingOptimizer';
import CommandPalette from './components/ui/CommandPalette';

import './styles/core.css'; // Core design system and dashboard styles
import './styles/navigation.css'; // Navigation effects and performance
import './styles/responsive.css'; // Responsive and mobile-first design
import './styles/accessibility-enhanced.css'; // Professional accessibility enhancements

// Lazy load pages for code splitting with enhanced configurations
const Dashboard = createLazyRoute(() => import('./pages/ModernDashboardPage'), LazyRouteConfigs.critical);
const Analytics = createLazyRoute(() => import('./pages/Analytics'), LazyRouteConfigs.standard);
const Login = createLazyRoute(() => import('./pages/Login'), LazyRouteConfigs.critical);
const Clients = createLazyRoute(() => import('./pages/Clients'), LazyRouteConfigs.standard);
const Agents = createLazyRoute(() => import('./pages/Agents'), LazyRouteConfigs.standard);
const Ledger = createLazyRoute(() => import('./pages/Ledger'), LazyRouteConfigs.standard);
const Settings = createLazyRoute(() => import('./pages/Settings'), LazyRouteConfigs.standard);
const Reports = createLazyRoute(() => import('./pages/Reports'), LazyRouteConfigs.heavy);
const BusinessAnalytics = createLazyRoute(() => import('./pages/BusinessAnalytics'), LazyRouteConfigs.heavy);
const SystemMonitor = createLazyRoute(() => import('./pages/SystemMonitor'), LazyRouteConfigs.heavy);
const Transactions = createLazyRoute(() => import('./pages/Transactions'), LazyRouteConfigs.standard);
const AddTransaction = createLazyRoute(() => import('./pages/AddTransaction'), LazyRouteConfigs.standard);
const Accounting = createLazyRoute(() => import('./pages/Accounting'), LazyRouteConfigs.standard);
const RevenueAnalytics = createLazyRoute(() => import('./pages/RevenueAnalytics'), LazyRouteConfigs.heavy);
const Future = createLazyRoute(() => import('./pages/Future'), LazyRouteConfigs.onDemand);
const TabShowcase = createLazyRoute(() => import('./components/TabShowcase'), LazyRouteConfigs.onDemand);

function App() {
  // Enable scroll restoration
  useScrollRestoration();

  // Preload critical components and setup performance optimization
  useEffect(() => {
    // Preload critical components after initial load
    const timer = setTimeout(async () => {
      await preloadComponents();
      // Start optimization based on usage patterns
      lazyLoadingOptimizer.preloadBasedOnPatterns();
    }, 1000);

    // Setup performance monitoring
    performanceOptimizer.setupLazyImages();

    // Cleanup on unmount
    return () => {
      clearTimeout(timer);
      performanceOptimizer.cleanup();
      lazyLoadingOptimizer.cleanup();
    };
  }, []);

  return (
    <Provider store={store}>
      <SWRConfig value={swrConfig}>
        <EnhancedErrorBoundary>
          <AuthProvider>
            <LanguageProvider>
              <NavigationProvider>
                <AccessibilityProvider>
                  <NotificationProvider position="top-right" maxVisible={5}>
                  <SkipLink />
                  <NavigationLoadingIndicator />
                  <CommandPalette />

                  <div className='min-h-screen bg-slate-50'>
                    <Suspense fallback={<LoadingSpinner />}>
                      <Routes>
                        <Route path='/login' element={<Login />} />
                        <Route
                          path='/'
                          element={
                            <ProtectedRoute>
                              <Layout />
                            </ProtectedRoute>
                          }
                        >
                          <Route index element={<Dashboard />} />
                          <Route path='dashboard' element={<Dashboard />} />
                          <Route path='clients' element={<Clients />} />
                          <Route path='accounting' element={<Accounting />} />
                          <Route path='ledger' element={<Ledger />} />
                          <Route path='transactions/add' element={<AddTransaction />} />
                          <Route path='transactions/clients' element={<Navigate to="/clients" replace />} />
                          
                          {/* Legacy route redirects for backward compatibility */}
                          <Route path='agents' element={<Agents />} />
                          
                          <Route path='analytics' element={<Analytics />} />
                          <Route path='revenue-analytics' element={<RevenueAnalytics />} />
                          <Route path='future' element={<Future />} />
                          <Route path='tab-showcase' element={<TabShowcase />} />
                          <Route path='settings' element={<Settings />} />
                          <Route path='reports' element={<Reports />} />
                          <Route
                            path='business-analytics'
                            element={<BusinessAnalytics />}
                          />
                          <Route
                            path='system-monitor'
                            element={<SystemMonitor />}
                          />
                          
                          {/* Legacy route redirects for backward compatibility */}
                          <Route path='/' element={<Navigate to="/dashboard" replace />} />

                          {/* Admin Routes (protected with admin requirement) */}
                          <Route
                            path='admin/users'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>User Management</h1>
                                <p>User management features coming soon...</p>
                              </div>
                            }
                          />
                          <Route
                            path='admin/permissions'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>Permissions</h1>
                                <p>Permissions management coming soon...</p>
                              </div>
                            }
                          />
                          <Route
                            path='admin/monitoring'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>System Monitoring</h1>
                                <p>System monitoring features coming soon...</p>
                              </div>
                            }
                          />
                          <Route
                            path='admin/database'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>Database Management</h1>
                                <p>Database management features coming soon...</p>
                              </div>
                            }
                          />
                          <Route
                            path='admin/backup'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>Backup & Restore</h1>
                                <p>Backup and restore features coming soon...</p>
                              </div>
                            }
                          />
                          <Route
                            path='admin/security'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>Security Settings</h1>
                                <p>Security settings coming soon...</p>
                              </div>
                            }
                          />
                          <Route
                            path='admin/logs'
                            element={
                              <div className='p-6'>
                                <h1 className='text-2xl font-bold'>System Logs</h1>
                                <p>System logs viewer coming soon...</p>
                              </div>
                            }
                          />
                        </Route>
                      </Routes>
                    </Suspense>
                  </div>
                  </NotificationProvider>
                </AccessibilityProvider>
              </NavigationProvider>
            </LanguageProvider>
          </AuthProvider>
        </EnhancedErrorBoundary>
      </SWRConfig>
      {/* Performance Widget - Sadece development modunda gosterilir */}
      {import.meta.env.DEV && (
        <PerformanceWidget 
          position="floating"
          compact={true}
          onPerformanceIssue={(metrics) => {
            // Performance sorunlarini sadece ciddi durumlarda log et
            if (metrics.renderTime && metrics.renderTime > 500) {
              console.warn('Severe performance issue detected:', metrics);
            }
          }}
        />
      )}
    </Provider>
  );
}

export default App;
