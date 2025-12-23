import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy, useEffect } from 'react';
import { SWRConfig } from 'swr';
import { Provider } from 'react-redux';
import { ThemeProvider } from 'next-themes';
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
import { initializeUIUXDebugging } from './utils/uiDebugInstrumentation';

import './styles/core.css'; // Core design system and dashboard styles
import './styles/navigation.css'; // Navigation effects and performance
import './styles/responsive.css'; // Responsive and mobile-first design
import './styles/accessibility-enhanced.css'; // Professional accessibility enhancements

// Lazy load pages for code splitting with enhanced configurations
const Dashboard = createLazyRoute(() => import('./pages/ModernDashboardPage'), LazyRouteConfigs.critical);
const Analytics = createLazyRoute(() => import('./pages/Analytics'), LazyRouteConfigs.standard);
const Login = createLazyRoute(() => import('./pages/Login'), LazyRouteConfigs.critical);
const Clients = createLazyRoute(() => import('./pages/Clients'), LazyRouteConfigs.standard);
const ClientDetail = createLazyRoute(() => import('./pages/ClientDetail'), LazyRouteConfigs.standard);
const Agents = createLazyRoute(() => import('./pages/Agents'), LazyRouteConfigs.standard);
const Ledger = createLazyRoute(() => import('./pages/Ledger'), LazyRouteConfigs.standard);
const Settings = createLazyRoute(() => import('./pages/Settings'), LazyRouteConfigs.standard);
const UserManagement = createLazyRoute(() => import('./pages/UserManagement'), LazyRouteConfigs.standard);
const Reports = createLazyRoute(() => import('./pages/Reports'), LazyRouteConfigs.heavy);
const BusinessAnalytics = createLazyRoute(() => import('./pages/BusinessAnalytics'), LazyRouteConfigs.heavy);
const SystemMonitor = createLazyRoute(() => import('./pages/SystemMonitor'), LazyRouteConfigs.heavy);
const Transactions = createLazyRoute(() => import('./pages/Transactions'), LazyRouteConfigs.standard);
const AddTransaction = createLazyRoute(() => import('./pages/AddTransaction'), LazyRouteConfigs.standard);
const Accounting = createLazyRoute(() => import('./pages/Accounting'), LazyRouteConfigs.standard);
const RevenueAnalytics = createLazyRoute(() => import('./pages/RevenueAnalytics'), LazyRouteConfigs.heavy);
const Trust = createLazyRoute(() => import('./pages/Trust'), LazyRouteConfigs.standard);
// AI Assistant page (legacy path `/future` kept for backward compatibility)
const AI = createLazyRoute(() => import('./pages/Future'), LazyRouteConfigs.onDemand);
const AdminSettings = createLazyRoute(() => import('./pages/AdminSettings'), LazyRouteConfigs.standard);
const TabShowcase = createLazyRoute(() => import('./components/TabShowcase'), LazyRouteConfigs.onDemand);
// Multi-tenancy admin pages
const Organizations = createLazyRoute(() => import('./pages/admin/Organizations'), LazyRouteConfigs.standard);
const Users = createLazyRoute(() => import('./pages/admin/Users'), LazyRouteConfigs.standard);

function App() {
  // Enable scroll restoration
  useScrollRestoration();

  // Preload critical components and setup performance optimization
  useEffect(() => {
    // #region agent log (dev only)
    if (import.meta.env.DEV) {
      fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.tsx:55',message:'App component mounted - UI/UX analysis start',data:{viewportWidth:window.innerWidth,viewportHeight:window.innerHeight,userAgent:navigator.userAgent,colorScheme:window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B,C,D'})}).catch(()=>{});
    }
    // #endregion
    
    // Preload critical components after initial load
    const timer = setTimeout(async () => {
      await preloadComponents();
      // Start optimization based on usage patterns
      lazyLoadingOptimizer.preloadBasedOnPatterns();
      
      // #region agent log (dev only)
      if (import.meta.env.DEV) {
        fetch('/api/v1/monitoring/client-log',{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'App.tsx:62',message:'Components preloaded - checking computed styles',data:{bodyBgColor:getComputedStyle(document.body).backgroundColor,bodyColor:getComputedStyle(document.body).color,rootPrimary:getComputedStyle(document.documentElement).getPropertyValue('--color-primary-500'),rootPrimaryAlt:getComputedStyle(document.documentElement).getPropertyValue('--business-primary')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,B'})}).catch(()=>{});
      }
      // #endregion
    }, 1000);

    // Setup performance monitoring
    performanceOptimizer.setupLazyImages();

    // Initialize UI/UX debugging (dev only)
    if (import.meta.env.DEV) {
      initializeUIUXDebugging();
    }

    // Cleanup on unmount
    return () => {
      clearTimeout(timer);
      performanceOptimizer.cleanup();
      lazyLoadingOptimizer.cleanup();
    };
  }, []);

  return (
    <Provider store={store}>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={true} disableTransitionOnChange={false}>
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

                  <div className='min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200'>
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
                          <Route path='clients/:clientName' element={<ClientDetail />} />
                          <Route path='accounting' element={<Accounting />} />
                          <Route path='finance/accounting' element={<Accounting />} />
                          <Route path='trust' element={<Trust />} />
                          <Route path='psp' element={<Ledger />} />
                          <Route path='ledger' element={<Navigate to="/psp" replace />} />
                          <Route path='transactions/add' element={<AddTransaction />} />
                          <Route path='transactions/clients' element={<Navigate to="/clients" replace />} />
                          
                          {/* Legacy route redirects for backward compatibility */}
                          <Route path='agents' element={<Agents />} />
                          
                          <Route path='analytics' element={<Analytics />} />
                          <Route path='revenue-analytics' element={<RevenueAnalytics />} />
                          <Route path='ai' element={<AI />} />
                          <Route path='future' element={<Navigate to="/ai" replace />} />
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
                          <Route path='admin' element={<Navigate to="/admin/settings" replace />} />
                          <Route path='admin/organizations' element={<Organizations />} />
                          <Route path='admin/users' element={<Users />} />
                          <Route path='admin/user-management' element={<UserManagement />} />
                          <Route path='admin/settings' element={<AdminSettings />} />
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
      </ThemeProvider>
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
