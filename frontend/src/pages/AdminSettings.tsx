import { useEffect, useState, lazy, Suspense } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Database, Monitor, RefreshCw, Shield, Building2, Users } from 'lucide-react';
import EnhancedErrorBoundary from '../components/EnhancedErrorBoundary';
import LoadingSpinner from '../components/LoadingSpinner';
import { SectionHeader } from '../components/ui/SectionHeader';
import { useLanguage } from '../contexts/LanguageContext';

// Lazy load components with error handling (mirrors Settings.tsx)
const SystemMonitor = lazy(() => import('./SystemMonitor').catch(err => {
  console.error('Failed to load SystemMonitor:', err);
  return { default: () => <div className="p-6 text-red-600">Failed to load System Monitor component</div> };
}));

const DatabaseManagement = lazy(() => import('../components/DatabaseManagement').catch(err => {
  console.error('Failed to load DatabaseManagement:', err);
  return { default: () => <div className="p-6 text-red-600">Failed to load Database Management component</div> };
}));

const SecurityManagement = lazy(() => import('../components/SecurityManagement').catch(err => {
  console.error('Failed to load SecurityManagement:', err);
  return { default: () => <div className="p-6 text-red-600">Failed to load Security Management component</div> };
}));

type AdminSettingsView = 'home' | 'monitor' | 'database' | 'security';

export default function AdminSettings() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [view, setView] = useState<AdminSettingsView>('home');

  // Sync view with URL (?view=monitor|database|security)
  useEffect(() => {
    const urlView = searchParams.get('view');
    if (urlView === 'monitor' || urlView === 'database' || urlView === 'security') {
      setView(urlView);
    } else {
      setView('home');
    }
  }, [searchParams]);

  const setUrlView = (next: AdminSettingsView) => {
    const nextParams = new URLSearchParams(searchParams);
    if (next === 'home') nextParams.delete('view');
    else nextParams.set('view', next);
    setSearchParams(nextParams, { replace: true });
  };

  const backToHome = () => setUrlView('home');

  return (
    <EnhancedErrorBoundary>
      <div className="p-6">
        <div className="mb-6">
          <SectionHeader
            title={t('settings.admin')}
            description={t('settings.system_administration')}
            icon={Shield}
          />
        </div>

        {view === 'home' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:border-gray-300 hover:shadow-sm"
              onClick={() => navigate('/admin/organizations')}
            >
              <Building2 className="h-7 w-7 text-blue-600 mb-2" />
              <h4 className="font-medium text-gray-900 text-sm">Organizations</h4>
              <p className="text-xs text-gray-500">Manage organizations and subscriptions</p>
            </div>

            <div
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:border-gray-300 hover:shadow-sm"
              onClick={() => navigate('/admin/users')}
            >
              <Users className="h-7 w-7 text-green-600 mb-2" />
              <h4 className="font-medium text-gray-900 text-sm">Users</h4>
              <p className="text-xs text-gray-500">Manage user accounts and permissions</p>
            </div>

            <div
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:border-gray-300 hover:shadow-sm"
              onClick={() => navigate('/admin/permissions')}
            >
              <Shield className="h-7 w-7 text-gray-600 mb-2" />
              <h4 className="font-medium text-gray-900 text-sm">{t('settings.permissions')}</h4>
              <p className="text-xs text-gray-500">{t('settings.configure_access_controls')}</p>
            </div>

            <div
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:border-gray-300 hover:shadow-sm"
              onClick={() => setUrlView('monitor')}
            >
              <Monitor className="h-7 w-7 text-gray-600 mb-2" />
              <h4 className="font-medium text-gray-900 text-sm">{t('settings.system_monitor')}</h4>
              <p className="text-xs text-gray-500">{t('settings.realtime_system_monitoring')}</p>
            </div>

            <div
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:border-gray-300 hover:shadow-sm"
              onClick={() => setUrlView('database')}
            >
              <Database className="h-7 w-7 text-gray-600 mb-2" />
              <h4 className="font-medium text-gray-900 text-sm">{t('settings.database')}</h4>
              <p className="text-xs text-gray-500">{t('settings.database_management')}</p>
            </div>

            <div
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:border-gray-300 hover:shadow-sm"
              onClick={() => setUrlView('security')}
            >
              <Shield className="h-7 w-7 text-gray-600 mb-2" />
              <h4 className="font-medium text-gray-900 text-sm">{t('settings.security')}</h4>
              <p className="text-xs text-gray-500">{t('settings.security_config')}</p>
            </div>
          </div>
        )}

        {view !== 'home' && (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <button
                onClick={backToHome}
                className="inline-flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors duration-200"
              >
                <span>←</span>
                Back
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div className="flex items-center gap-2">
                {view === 'monitor' && <Monitor className="h-5 w-5 text-slate-700" />}
                {view === 'database' && <Database className="h-5 w-5 text-slate-700" />}
                {view === 'security' && <Shield className="h-5 w-5 text-slate-700" />}
                <h3 className="text-lg font-medium text-gray-900">
                  {view === 'monitor' ? 'System Monitor' : view === 'database' ? 'Database Management' : 'Security Management'}
                </h3>
              </div>
            </div>

            <div className={view === 'database' ? 'bg-white rounded-lg border border-gray-200 overflow-hidden p-6' : 'bg-white rounded-lg border border-gray-200 overflow-hidden'}>
              <EnhancedErrorBoundary>
                <Suspense
                  fallback={
                    view === 'database' ? (
                      <div className="flex items-center justify-center p-12">
                        <RefreshCw className="h-8 w-8 animate-spin text-slate-700" />
                      </div>
                    ) : (
                      <LoadingSpinner />
                    )
                  }
                >
                  {view === 'monitor' && <SystemMonitor />}
                  {view === 'database' && <DatabaseManagement />}
                  {view === 'security' && <SecurityManagement />}
                </Suspense>
              </EnhancedErrorBoundary>
            </div>
          </div>
        )}
      </div>
    </EnhancedErrorBoundary>
  );
}


