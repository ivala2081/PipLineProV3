/**
 * Unified Navigation Component
 * Single component that handles both desktop sidebar and mobile navigation
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useNavigation } from '../../contexts/NavigationContext';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import LanguageSwitcher from '../LanguageSwitcher';
import { 
  Menu, 
  X, 
  ChevronDown, 
  Bell, 
  User,
  LogOut,
  Clock,
  Activity
} from 'lucide-react';
import { clsx } from 'clsx';

interface UnifiedNavigationProps {
  variant: 'sidebar' | 'mobile-bottom' | 'mobile-drawer';
  className?: string;
}

export const UnifiedNavigation: React.FC<UnifiedNavigationProps> = ({ 
  variant, 
  className = '' 
}) => {
  const { state, navigationItems, isActive, navigateTo, getMobileNavigation } = useNavigation();
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuOpen) {
        const target = event.target as Element;
        if (!target.closest('[data-user-menu]')) {
          setUserMenuOpen(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [userMenuOpen]);

  const handleItemClick = (item: any) => {
    if (item.children) {
      // Toggle expansion for items with children
      const newExpanded = new Set(expandedItems);
      if (newExpanded.has(item.id)) {
        newExpanded.delete(item.id);
      } else {
        newExpanded.add(item.id);
      }
      setExpandedItems(newExpanded);
    } else {
      // Navigate to the path
      navigateTo(item.href);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Desktop Sidebar
  if (variant === 'sidebar') {
    return (
      <div className={clsx('flex flex-col h-full bg-white border-r border-gray-200', className)}>
        {/* Logo Section */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <img 
              src="/plogo.png" 
              alt="PipLinePro" 
              className="w-8 h-8 rounded-lg"
            />
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{t('common.app_name')}</h1>
              <p className="text-xs text-gray-500">{t('common.financial_management')}</p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            const hasChildren = item.children && item.children.length > 0;
            const isExpanded = expandedItems.has(item.id);

            return (
              <div key={item.id}>
                <button
                  onClick={() => handleItemClick(item)}
                  className={clsx(
                    'w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                    item.special
                      ? active
                        ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg'
                        : 'text-purple-600 hover:bg-purple-50 hover:text-purple-700'
                      : active
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={clsx(
                      'w-5 h-5',
                      item.special && active && 'animate-pulse'
                    )} />
                    <span>{item.name}</span>
                    {item.badge && (
                      <Badge 
                        variant={item.special ? 'default' : 'secondary'}
                        className={clsx(
                          'text-xs',
                          item.special && 'bg-white/20 text-white'
                        )}
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </div>
                  {hasChildren && (
                    <ChevronDown 
                      className={clsx(
                        'w-4 h-4 transition-transform',
                        isExpanded && 'rotate-180'
                      )} 
                    />
                  )}
                </button>

                {/* Submenu */}
                {hasChildren && isExpanded && (
                  <div className="ml-8 mt-2 space-y-1">
                    {item.children!.map((child) => {
                      const ChildIcon = child.icon;
                      const childActive = isActive(child.href);
                      
                      return (
                        <button
                          key={child.id}
                          onClick={() => navigateTo(child.href)}
                          className={clsx(
                            'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                            childActive
                              ? 'bg-gray-100 text-gray-900'
                              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                          )}
                        >
                          <ChildIcon className="w-4 h-4" />
                          <span>{child.name}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.username || 'User'}
              </p>
              <p className="text-xs text-gray-500">
                {user?.role || 'User'}
              </p>
            </div>
            <div className="relative" data-user-menu>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="w-8 h-8 p-0"
              >
                <ChevronDown className="w-4 h-4" />
              </Button>
              
              {userMenuOpen && (
                <div className="absolute right-0 bottom-full mb-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    <LogOut className="w-4 h-4" />
                    {t('common.sign_out')}
                  </button>
                </div>
              )}
            </div>
          </div>
          
          {/* Language Switcher */}
          <div className="mb-3">
            <LanguageSwitcher variant="button" className="w-full justify-center" />
          </div>
          
          {/* System Status */}
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>{t('common.system_online')}</span>
            <Clock className="w-3 h-3 ml-auto" />
            <span>{currentTime.toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    );
  }

  // Mobile Bottom Navigation
  if (variant === 'mobile-bottom') {
    const mobileItems = getMobileNavigation();

    return (
      <div className={clsx(
        'lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50',
        className
      )}>
        <div className="flex items-center justify-around px-2 py-2">
          {mobileItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            
            return (
              <button
                key={item.id}
                onClick={() => navigateTo(item.href)}
                className={clsx(
                  'flex flex-col items-center justify-center p-2 rounded-lg transition-all duration-200 min-w-[60px] min-h-[60px] relative',
                  item.special
                    ? active
                      ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                      : 'text-purple-600'
                    : active
                    ? 'text-gray-900 bg-gray-100'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                )}
              >
                {/* Special effects for Future nav */}
                {item.special && active && (
                  <div className="absolute inset-0 rounded-lg overflow-hidden">
                    <div className="absolute top-1 right-1 w-1 h-1 bg-white rounded-full animate-ping" />
                    <div className="absolute bottom-1 left-1 w-0.5 h-0.5 bg-white rounded-full animate-ping" style={{ animationDelay: '1s' }} />
                  </div>
                )}
                
                <div className="relative z-10">
                  <Icon className={clsx(
                    'transition-all duration-200',
                    item.special
                      ? clsx(
                          'h-6 w-6',
                          active && 'animate-pulse drop-shadow-sm'
                        )
                      : clsx(
                          'h-5 w-5',
                          active && 'scale-105'
                        )
                  )} />
                  {item.badge && (
                    <Badge 
                      className={clsx(
                        'absolute -top-2 -right-2 h-4 w-4 text-xs p-0 flex items-center justify-center',
                        item.special
                          ? 'bg-white/20 text-white'
                          : 'bg-red-500 text-white'
                      )}
                    >
                      {item.badge}
                    </Badge>
                  )}
                </div>
                
                <span className={clsx(
                  'text-xs font-medium mt-1 text-center z-10',
                  item.special && active && 'text-white drop-shadow-sm'
                )}>
                  {item.name}
                </span>
              </button>
            );
          })}
          
          {/* Quick Actions Button */}
          <button className="flex flex-col items-center justify-center p-2 rounded-lg transition-all duration-200 min-w-[60px] min-h-[60px] text-gray-600 hover:text-gray-900 hover:bg-gray-50">
            <div className="relative">
              <Activity className="h-5 w-5 transition-transform duration-200 hover:scale-105" />
            </div>
            <span className="text-xs font-medium mt-1 text-center">
              More
            </span>
          </button>
        </div>
      </div>
    );
  }

  // Mobile Drawer
  if (variant === 'mobile-drawer') {
    return (
      <div className={clsx(
        'lg:hidden fixed inset-0 bg-white z-50 transform transition-transform duration-300 ease-in-out',
        state.mobileMenuOpen ? 'translate-x-0' : '-translate-x-full',
        className
      )}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <img 
              src="/plogo.png" 
              alt="PipLinePro" 
              className="w-8 h-8 rounded-lg"
            />
            <h2 className="text-lg font-semibold text-gray-900">Menu</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateTo('/')}
            className="w-8 h-8 p-0"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            const hasChildren = item.children && item.children.length > 0;
            const isExpanded = expandedItems.has(item.id);

            return (
              <div key={item.id}>
                <button
                  onClick={() => handleItemClick(item)}
                  className={clsx(
                    'w-full flex items-center justify-between px-3 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                    item.special
                      ? active
                        ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                        : 'text-purple-600 hover:bg-purple-50'
                      : active
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5" />
                    <span>{item.name}</span>
                    {item.badge && (
                      <Badge variant="secondary" className="text-xs">
                        {item.badge}
                      </Badge>
                    )}
                  </div>
                  {hasChildren && (
                    <ChevronDown 
                      className={clsx(
                        'w-4 h-4 transition-transform',
                        isExpanded && 'rotate-180'
                      )} 
                    />
                  )}
                </button>

                {/* Submenu */}
                {hasChildren && isExpanded && (
                  <div className="ml-8 mt-2 space-y-1">
                    {item.children!.map((child) => {
                      const ChildIcon = child.icon;
                      const childActive = isActive(child.href);
                      
                      return (
                        <button
                          key={child.id}
                          onClick={() => navigateTo(child.href)}
                          className={clsx(
                            'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                            childActive
                              ? 'bg-gray-100 text-gray-900'
                              : 'text-gray-600 hover:bg-gray-50'
                          )}
                        >
                          <ChildIcon className="w-4 h-4" />
                          <span>{child.name}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-gray-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.username || 'User'}
              </p>
              <p className="text-xs text-gray-500">
                {user?.role || 'User'}
              </p>
            </div>
          </div>
          
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign out
          </Button>
        </div>
      </div>
    );
  }

  return null;
};

export default UnifiedNavigation;
