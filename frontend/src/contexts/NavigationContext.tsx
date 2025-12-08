/**
 * Unified Navigation Context
 * Provides consistent navigation state and configuration across desktop and mobile
 */

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useNavigationLoading } from '../hooks/useNavigationLoading';
import { useLanguage } from './LanguageContext';
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
  Plus
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

// Unified navigation configuration
const navigationConfig: NavigationItem[] = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home,
    mobilePriority: 'high',
    description: 'Overview and key metrics'
  },
  {
    id: 'clients',
    name: 'Clients',
    href: '/clients',
    icon: FileText,
    mobilePriority: 'high',
    description: 'Client management and data'
  },
  {
    id: 'accounting',
    name: 'Accounting',
    href: '/accounting',
    icon: Calculator,
    mobilePriority: 'high',
    description: 'Financial accounting tools'
  },
  {
    id: 'ledger',
    name: 'Ledger',
    href: '/ledger',
    icon: ClipboardList,
    mobilePriority: 'high',
    description: 'Transaction ledger and records'
  },
  {
    id: 'analytics',
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    mobilePriority: 'medium',
    description: 'Data analysis and insights'
  },
  {
    id: 'future',
    name: 'Future',
    href: '/future',
    icon: Sparkles,
    mobilePriority: 'high',
    special: true,
    badge: 'AI',
    description: 'AI-powered features and insights'
  },
  {
    id: 'settings',
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    mobilePriority: 'low',
    description: 'Application settings and preferences'
  }
];

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
  '/ledger': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Ledger', href: '/ledger', current: true }
  ],
  '/analytics': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Analytics', href: '/analytics', current: true }
  ],
  '/future': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'AI Forecast', href: '/future', current: true }
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
  '/business-analytics': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Business Analytics', href: '/business-analytics', current: true }
  ],
  '/system-monitor': [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'System Monitor', href: '/system-monitor', current: true }
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
  
  const [state, setState] = useState<NavigationState>({
    currentPage: location.pathname,
    sidebarOpen: false,
    mobileMenuOpen: false,
    breadcrumbs: []
  });

  // Create translated navigation items that update when language changes
  const translatedNavigationItems = useMemo((): NavigationItem[] => [
    {
      id: 'dashboard',
      name: t('navigation.dashboard'),
      href: '/dashboard',
      icon: Home,
      mobilePriority: 'high',
      description: t('tabs.overview_desc')
    },
    {
      id: 'clients',
      name: t('navigation.clients'),
      href: '/clients',
      icon: FileText,
      mobilePriority: 'high',
      description: t('clients.description')
    },
    {
      id: 'accounting',
      name: t('navigation.accounting'),
      href: '/accounting',
      icon: Calculator,
      mobilePriority: 'high',
      description: t('accounting.description')
    },
    {
      id: 'ledger',
      name: t('navigation.ledger'),
      href: '/ledger',
      icon: ClipboardList,
      mobilePriority: 'high',
      description: t('ledger.description')
    },
    {
      id: 'analytics',
      name: t('analytics.title'),
      href: '/analytics',
      icon: BarChart3,
      mobilePriority: 'medium',
      description: t('analytics.description')
    },
    {
      id: 'future',
      name: t('navigation.advanced_features'),
      href: '/future',
      icon: Sparkles,
      mobilePriority: 'high',
      special: true,
      badge: 'AI',
      description: 'AI-powered features and insights'
    },
    {
      id: 'settings',
      name: t('navigation.settings'),
      href: '/settings',
      icon: Settings,
      mobilePriority: 'low',
      description: t('settings.subtitle')
    }
  ], [currentLanguage, t]);

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
    navigate(href);
  }, [navigate, setLoading]);

// Memoize isActive function
  const isActive = useCallback((href: string): boolean => {
    if (href === '/dashboard' && location.pathname === '/') {
      return true;
    }
    return location.pathname === href || location.pathname.startsWith(href + '/');
  }, [location.pathname]);

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
