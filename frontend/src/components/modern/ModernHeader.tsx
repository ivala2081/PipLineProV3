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

  const getUnreadCount = () => {
    return unreadCount;
  };


  return (
    <header style={{ height: '4rem', borderBottom: '1px solid #e5e7eb', backgroundColor: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 1.5rem' }} className="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-6">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="lg:hidden text-gray-600 hover:text-gray-900 hover:bg-gray-100"
        >
          <Menu className="w-5 h-5" />
        </Button>
        
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

      {/* Center Section - Reserved for future features */}
      <div className="hidden lg:flex items-center">
        {/* Future features will be added here */}
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
            className="relative text-gray-600 hover:text-gray-900 hover:bg-gray-100"
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
            <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-md z-50">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setNotificationsOpen(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-gray-500">
                    <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-sm">No notifications</p>
                  </div>
                ) : (
                  notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 cursor-pointer transition-colors ${
                        !notification.read ? 'bg-gray-50' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {notification.type === 'info' && <Info className="w-4 h-4 text-gray-500 mt-0.5" />}
                        {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5" />}
                        {notification.type === 'success' && <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="text-sm font-medium text-gray-900">{notification.title}</h4>
                            <span className="text-xs text-gray-500">{notification.time}</span>
                          </div>
                          <p className="text-sm text-gray-600">{notification.message}</p>
                          {!notification.read && (
                            <Badge variant="outline" className="mt-2 text-xs border-gray-200 text-gray-700">
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

        {/* User Menu */}
        <div className="relative">
          <Button
            variant="ghost"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          >
            <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <span className="hidden md:block text-sm font-medium">{user?.username || 'User'}</span>
            <ChevronDown className="w-4 h-4" />
          </Button>

          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-md z-50">
              <div className="p-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start text-gray-700 hover:text-gray-900 hover:bg-gray-50"
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
                  className="w-full justify-start text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                  onClick={() => {
                    setUserMenuOpen(false);
                    navigate('/settings');
                  }}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
                <div className="border-t border-gray-200 my-1" />
                <Button
                  variant="ghost"
                  className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
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
