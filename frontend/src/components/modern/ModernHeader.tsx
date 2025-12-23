import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Bell, 
  Settings, 
  User, 
  ChevronDown, 
  Menu,
  X,
  Search,
  Globe,
  LogOut,
  Info,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { GlobalSearch } from './GlobalSearch';
import { NotificationSystem } from './NotificationSystem';
import PerformanceWidget from '../PerformanceWidget';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../hooks/useNotifications';
import { BreadcrumbNavigation } from '../navigation/BreadcrumbNavigation';
// import { ThemeToggle } from '../ui/ThemeToggle'; // Temporarily disabled - will be improved later

interface ModernHeaderProps {
  onMenuClick: () => void;
  onLogout: () => void;
}

export const ModernHeader: React.FC<ModernHeaderProps> = ({ 
  onMenuClick, 
  onLogout 
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  
  // Use real notifications hook instead of hardcoded
  const { notifications, unreadCount } = useNotifications();

  // #region agent log
  React.useEffect(() => {
    if (!import.meta.env.DEV) return;
    const header = document.querySelector('header');
    if (header) {
      const computed = getComputedStyle(header);
      fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ModernHeader.tsx:47',message:'Header styles detected',data:{bgColor:computed.backgroundColor,hasGradient:computed.backgroundImage&&computed.backgroundImage!=='none',borderColor:computed.borderColor},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A,E'})}).catch(()=>{});
    }
    
    // Check focus states
    const checkFocusStates = () => {
      const focusable = document.querySelectorAll('button, a, input, [tabindex]');
      let hasBlueFocus = 0;
      focusable.forEach(el => {
        const computed = getComputedStyle(el);
        const focusStyle = window.getComputedStyle(el, ':focus-visible');
        if (focusStyle.outlineColor.includes('blue') || focusStyle.boxShadow.includes('blue') || focusStyle.borderColor.includes('blue')) {
          hasBlueFocus++;
        }
      });
      fetch('http://127.0.0.1:7242/ingest/49fd889e-f043-489a-b352-a05d8b26fc7c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ModernHeader.tsx:60',message:'Focus states check',data:{totalFocusable:focusable.length,hasBlueFocus},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
    };
    setTimeout(checkFocusStates, 2000);
  }, []);
  // #endregion

  const getUnreadCount = () => {
    return unreadCount;
  };

return (
    <header className="sticky top-0 z-50 p-6 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center justify-between w-full min-h-[88px] transition-colors duration-200">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="lg:hidden text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <Menu className="w-5 h-5" />
        </Button>
        
        <BreadcrumbNavigation />
        
        <div className="hidden lg:flex items-center">
          <GlobalSearch onResultClick={(result) => {
            // Navigate to result
            if (result.type === 'transaction') {
              navigate(`/transactions?highlight=${result.id}`);
            } else if (result.type === 'client') {
              navigate(`/clients?highlight=${result.id}`);
            }
          }} />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-2">
        {/* Performance Widget - Development Only */}
        {process.env.NODE_ENV === 'development' && (
          <PerformanceWidget position="header" compact={true} />
        )}
        
        {/* Notifications */}
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <Bell className="w-5 h-5" />
            {getUnreadCount() > 0 && (
              <Badge 
                variant="destructive" 
                className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center text-xs bg-red-600"
              >
                {getUnreadCount()}
              </Badge>
            )}
          </Button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md z-50">
              <div className="p-4 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Notifications</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setNotificationsOpen(false)}
                    className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                    <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                    <p className="text-sm">No notifications</p>
                  </div>
                ) : (
                  notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors ${
                        !notification.read ? 'bg-gray-50 dark:bg-gray-800' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {notification.type === 'info' && <Info className="w-4 h-4 text-gray-500 mt-0.5" />}
                        {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5" />}
                        {notification.type === 'success' && <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">{notification.title}</h4>
                            <span className="text-xs text-gray-500 dark:text-gray-400">{notification.time}</span>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-300">{notification.message}</p>
                          {!notification.read && (
                            <Badge variant="outline" className="mt-2 text-xs border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300">
                              New
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle - Temporarily disabled - will be improved later */}
        {/* <ThemeToggle /> */}

        {/* User Menu */}
        <div className="relative">
          <Button
            variant="ghost"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <div className="w-8 h-8 bg-gray-700 dark:bg-gray-600 rounded-lg flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <span className="hidden md:block text-sm font-medium">{user?.username || 'User'}</span>
            <ChevronDown className="w-4 h-4" />
          </Button>

          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-md z-50">
              <div className="p-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
                  onClick={() => {
                    setUserMenuOpen(false);
                    navigate('/settings?tab=profile');
                  }}
                >
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
                  onClick={() => {
                    setUserMenuOpen(false);
                    navigate('/settings');
                  }}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
                <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                <Button
                  variant="ghost"
                  className="w-full justify-start text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20"
                  onClick={() => {
                    setUserMenuOpen(false);
                    onLogout();
                  }}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign out
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
