/**
 * Unified Navigation Context
 * Provides consistent navigation state and configuration across desktop and mobile
 */

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useNavigationLoading } from '../hooks/useNavigationLoading';
import { useLanguage } from './LanguageContext';
import { useAuth } from './AuthContext';
import { 
  Home, 
  BarChart3, 
  FileText, 
  Settings, 
  Calculator,
  ClipboardList,
  Building2,
  Sparkles,
  Users,
  Plus,
  Activity,
  Shield,
  Wallet,
  Database,
  KeyRound,
  HardDriveDownload,
  ScrollText,
  Wrench
} from 'lucide-react';

export interface NavigationItem {
  id: string;
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number | string;
  mobilePriority: 'high' | 'medium' | 'low';
  special?: boolean;
  description?: string;
  children?: NavigationItem[];
  requiresAdmin?: boolean;
}

export interface NavigationState {
  currentPage: string;
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;
  breadcrumbs: BreadcrumbItem[];
}

export interface BreadcrumbItem {
  label: string;
  href: string;
  current?: boolean;
}

interface NavigationContextType {
  state: NavigationState;
  navigationItems: NavigationItem[];
  setSidebarOpen: (open: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
  navigateTo: (href: string) => void;
  getBreadcrumbs: (pathname: string) => BreadcrumbItem[];
  isActive: (href: string) => boolean;
  getMobileNavigation: () => NavigationItem[];
  isNavigating: boolean;
  loadingMessage: string;
  setLoading: (loading: boolean, message?: string) => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

// Note: navigation items are built inside the provider so we can use translations + role gating.

// Breadcrumb mapping for different routes
const breadcrumbMap: Record<string, BreadcrumbItem[]> = {
  '/': [
    { label: 'Dashboard', href: '/dashboard', current: true }
  ],
  '/dashboard': [
    { label: 'Dashboard', href: '/dashboard', current: true }
  ],
  '/clients': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Clients', href: '/clients', current: true }
  ],
  '/accounting': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Accounting', href: '/accounting', current: true }
  ],
  '/psp': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'PSP', href: '/psp', current: true }
  ],
  '/ledger': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'PSP', href: '/psp', current: true }
  ],
  '/analytics': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Analytics', href: '/analytics', current: true }
  ],
  '/ai': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'AI Assistant', href: '/ai', current: true }
  ],
  // Legacy path kept for backward compatibility
  '/future': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'AI Assistant', href: '/ai', current: true }
  ],
  '/settings': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Settings', href: '/settings', current: true }
  ],
  '/agents': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Agents', href: '/agents', current: true }
  ],
  '/reports': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Reports', href: '/reports', current: true }
  ],
  '/transactions': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Transactions', href: '/transactions', current: true }
  ],
  '/transactions/add': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Transactions', href: '/transactions' },
    { label: 'Add Transaction', href: '/transactions/add', current: true }
  ],
  '/revenue-analytics': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Revenue Analytics', href: '/revenue-analytics', current: true }
  ],
  '/business-analytics': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Business Analytics', href: '/business-analytics', current: true }
  ],
  '/system-monitor': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'System Monitor', href: '/system-monitor', current: true }
  ],
  '/admin/settings': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings', current: true }
  ],
  '/admin/users': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Users', href: '/admin/settings', current: true }
  ],
  '/admin/permissions': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Permissions', href: '/admin/permissions', current: true }
  ],
  '/admin/monitoring': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Monitoring', href: '/admin/monitoring', current: true }
  ],
  '/admin/database': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Database', href: '/admin/database', current: true }
  ],
  '/admin/backup': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Backup', href: '/admin/backup', current: true }
  ],
  '/admin/security': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Security', href: '/admin/security', current: true }
  ],
  '/admin/logs': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Admin', href: '/admin/settings' },
    { label: 'Logs', href: '/admin/logs', current: true }
  ]
};

interface NavigationProviderProps {
  children: ReactNode;
}

export const NavigationProvider: React.FC<NavigationProviderProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isNavigating, loadingMessage, setLoading } = useNavigationLoading();
  const { t, currentLanguage } = useLanguage();
  const { user } = useAuth();
  
  const [state, setState] = useState<NavigationState>({
    currentPage: location.pathname,
    sidebarOpen: false,
    mobileMenuOpen: false,
    breadcrumbs: []
  });

  // Create translated navigation items that update when language changes
  // Also exposes major page tabs as submenu items via `?tab=...` links and hides admin links for non-admin users.
  const translatedNavigationItems = useMemo((): NavigationItem[] => {
    // User is admin if role is 'admin' OR admin_level is 1, 2, or 3 (excluding hard admin level 0 for UI visibility)
    const isAdmin = (user?.role || '').toLowerCase() === 'admin' || (user?.admin_level !== undefined && user.admin_level >= 1 && user.admin_level <= 3);
    const tr = (key: string, fallback: string) => {
      const v = t(key);
      // In production builds, missing resources (or namespace issues) can yield empty strings.
      // Ensure navigation never renders empty labels.
      if (typeof v !== 'string') return fallback;
      const trimmed = v.trim();
      if (!trimmed || trimmed === key) return fallback;
      return trimmed;
    };

    const items: NavigationItem[] = [
      {
        id: 'dashboard',
        name: tr('navigation.dashboard', 'Dashboard'),
        href: '/dashboard',
        icon: Home,
        mobilePriority: 'high',
        description: tr('tabs.overview_desc', 'Dashboard overview and key metrics')
      },
      {
        id: 'clients',
        name: tr('navigation.clients', 'Clients'),
        href: '/clients',
        icon: Users,
        mobilePriority: 'high',
        description: tr('clients.description', 'Client management and data')
      },
      {
        id: 'finance',
        name: 'Finance',
        href: '/accounting',
        icon: Calculator,
        mobilePriority: 'medium',
        description: 'Accounting and ledger',
        children: [
          {
            id: 'accounting',
            name: t('navigation.accounting'),
            href: '/accounting',
            icon: Calculator,
            mobilePriority: 'medium',
            description: t('accounting.description'),
            children: [
              { id: 'accounting-overview', name: t('tabs.overview'), href: '/accounting?tab=overview', icon: BarChart3, mobilePriority: 'low' },
              { id: 'accounting-expenses', name: t('tabs.expenses'), href: '/accounting?tab=expenses', icon: FileText, mobilePriority: 'low' },
              { id: 'accounting-net', name: t('tabs.net'), href: '/accounting?tab=net', icon: Calculator, mobilePriority: 'low' },
              { id: 'accounting-analytics', name: `${t('navigation.accounting')} ${t('tabs.analytics')}`, href: '/accounting?tab=analytics', icon: BarChart3, mobilePriority: 'low' },
            ]
          },
          {
            id: 'trust',
            name: t('tabs.trust'),
            href: '/trust',
            icon: Wallet,
            mobilePriority: 'medium',
            description: t('tabs.trust'),
          },
          {
            id: 'psp',
            name: t('navigation.psp', 'PSP'),
            href: '/psp',
            icon: ClipboardList,
            mobilePriority: 'medium',
            description: t('ledger.description'),
            children: [
              { id: 'psp-overview', name: t('tabs.overview'), href: '/psp?tab=overview', icon: ClipboardList, mobilePriority: 'low' },
              { id: 'psp-monthly', name: t('tabs.monthly'), href: '/psp?tab=monthly', icon: ClipboardList, mobilePriority: 'low' },
              { id: 'psp-analytics', name: `${t('navigation.psp', 'PSP')} ${t('tabs.analytics')}`, href: '/psp?tab=analytics', icon: BarChart3, mobilePriority: 'low' },
            ]
          }
        ]
      },
      {
        id: 'analytics-group',
        name: tr('analytics.group_title', 'Analytics & Reports'),
        href: '/analytics',
        icon: BarChart3,
        mobilePriority: 'low',
        description: 'Insights and reporting',
        children: [
          { id: 'analytics', name: t('analytics.title'), href: '/analytics', icon: BarChart3, mobilePriority: 'low', description: t('analytics.description') },
          { id: 'revenue-analytics', name: tr('analytics.revenue_analytics', 'Revenue Analytics'), href: '/revenue-analytics', icon: BarChart3, mobilePriority: 'low' },
          { id: 'reports', name: tr('reports.title', 'Reports'), href: '/reports', icon: FileText, mobilePriority: 'low' },
          { id: 'business-analytics', name: tr('analytics.business_analytics', 'Business Analytics'), href: '/business-analytics', icon: Building2, mobilePriority: 'low' },
        ]
      },
      {
        id: 'ai',
        name: 'Future',
        href: '/ai',
        icon: Sparkles,
        mobilePriority: 'medium',
        badge: 'AI',
        description: 'AI-powered features and insights'
      },
      {
        id: 'system',
        name: 'System',
        href: '/settings',
        icon: Wrench,
        mobilePriority: 'low',
        description: 'System settings and monitoring',
        children: [
          { id: 'system-monitor', name: 'System Monitor', href: '/system-monitor', icon: Activity, mobilePriority: 'low' },
          {
            id: 'settings',
            name: t('navigation.settings'),
            href: '/settings',
            icon: Settings,
            mobilePriority: 'low',
            description: t('settings.subtitle'),
            children: [
              { id: 'settings-general', name: t('settings.general'), href: '/settings?tab=general', icon: Settings, mobilePriority: 'low' },
              { id: 'settings-dropdowns', name: t('settings.dropdowns'), href: '/settings?tab=dropdowns', icon: FileText, mobilePriority: 'low' },
              { id: 'settings-departments', name: t('settings.departments'), href: '/settings?tab=departments', icon: Building2, mobilePriority: 'low' },
              { id: 'settings-notifications', name: t('settings.notifications'), href: '/settings?tab=notifications', icon: Activity, mobilePriority: 'low' },
              { id: 'settings-integrations', name: t('settings.integrations'), href: '/settings?tab=integrations', icon: Wrench, mobilePriority: 'low' },
              { id: 'settings-translations', name: t('settings.translations'), href: '/settings?tab=translations', icon: ScrollText, mobilePriority: 'low' },
            ]
          },
          ...(isAdmin ? [{
            id: 'admin',
            name: 'Admin',
            href: '/admin/settings',
            icon: Shield,
            mobilePriority: 'low',
            requiresAdmin: true,
            children: [
              { id: 'admin-users', name: 'Users', href: '/admin/settings', icon: Users, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-settings', name: t('settings.admin'), href: '/admin/settings', icon: Settings, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-permissions', name: 'Permissions', href: '/admin/permissions', icon: KeyRound, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-monitoring', name: 'Monitoring', href: '/admin/monitoring', icon: Activity, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-database', name: 'Database', href: '/admin/database', icon: Database, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-backup', name: 'Backup', href: '/admin/backup', icon: HardDriveDownload, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-security', name: 'Security', href: '/admin/security', icon: Shield, mobilePriority: 'low', requiresAdmin: true },
              { id: 'admin-logs', name: 'Logs', href: '/admin/logs', icon: ScrollText, mobilePriority: 'low', requiresAdmin: true },
            ]
          }] : []),
        ]
      }
    ];

    // Filter admin-only items if somehow included
    const filterAdmin = (navItems: NavigationItem[]): NavigationItem[] =>
      navItems
        .filter(i => !i.requiresAdmin || isAdmin)
        .map(i => i.children ? ({ ...i, children: filterAdmin(i.children) }) : i);

    return filterAdmin(items);
  }, [currentLanguage, t, user?.role]);

  // Define getBreadcrumbs function first
  const getBreadcrumbs = useCallback((pathname: string): BreadcrumbItem[] => {
    // Check for exact match first
    if (breadcrumbMap[pathname]) {
      return breadcrumbMap[pathname];
    }

    // Check for dynamic routes (e.g., /clients/123)
    const pathSegments = pathname.split('/').filter(Boolean);
    if (pathSegments.length > 1) {
      const basePath = `/${pathSegments[0]}`;
      if (breadcrumbMap[basePath]) {
        const breadcrumbs = [...breadcrumbMap[basePath]];
        // Add dynamic segment
        const dynamicSegment = pathSegments[pathSegments.length - 1];
        breadcrumbs.push({
          label: dynamicSegment.charAt(0).toUpperCase() + dynamicSegment.slice(1),
          href: pathname,
          current: true
        });
        return breadcrumbs;
      }
    }

    // Default breadcrumb
    return [{ label: 'Dashboard', href: '/dashboard', current: true }];
  }, []);

  // Memoize breadcrumbs calculation to prevent unnecessary recalculations
  const breadcrumbs = useMemo(() => {
    return getBreadcrumbs(location.pathname);
  }, [location.pathname, getBreadcrumbs]);

  // Update current page and breadcrumbs when location changes
  useEffect(() => {
    setState(prev => ({
      ...prev,
      currentPage: location.pathname,
      breadcrumbs,
      sidebarOpen: false, // Close sidebar on navigation
      mobileMenuOpen: false // Close mobile menu on navigation
    }));
  }, [location.pathname, breadcrumbs]);

  // Memoize callback functions to prevent unnecessary re-renders
  const setSidebarOpen = useCallback((open: boolean) => {
    setState(prev => ({ ...prev, sidebarOpen: open }));
  }, []);

  const setMobileMenuOpen = useCallback((open: boolean) => {
    setState(prev => ({ ...prev, mobileMenuOpen: open }));
  }, []);

  const navigateTo = useCallback((href: string) => {
    setLoading(true, 'Navigating...');
    // Temporary debugging for sidebar navigation issues
    // eslint-disable-next-line no-console
    console.log('[navigateTo]', {
      from: `${location.pathname}${location.search || ''}`,
      to: href
    });
    navigate(href);
  }, [navigate, setLoading, location.pathname, location.search]);

  // Memoize isActive function
  // Supports query-string navigation items (e.g. /clients?tab=transactions)
  const isActive = useCallback((href: string): boolean => {
    const current = `${location.pathname}${location.search || ''}`;

    if (href === '/dashboard' && location.pathname === '/') {
      return true;
    }

    if (href.includes('?')) {
      return current === href;
    }

    return location.pathname === href || location.pathname.startsWith(href + '/');
  }, [location.pathname, location.search]);

  // Memoize getMobileNavigation function
  const getMobileNavigation = useCallback((): NavigationItem[] => {
    return translatedNavigationItems.filter(item => item.mobilePriority === 'high');
  }, [translatedNavigationItems]);

  // Memoize the context value to prevent unnecessary re-renders
  const value: NavigationContextType = useMemo(() => ({
    state,
    navigationItems: translatedNavigationItems,
    setSidebarOpen,
    setMobileMenuOpen,
    navigateTo,
    getBreadcrumbs,
    isActive,
    getMobileNavigation,
    isNavigating,
    loadingMessage,
    setLoading
  }), [state, translatedNavigationItems, setSidebarOpen, setMobileMenuOpen, navigateTo, getBreadcrumbs, isActive, getMobileNavigation, isNavigating, loadingMessage, setLoading]);

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
};

export const useNavigation = (): NavigationContextType => {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
};
