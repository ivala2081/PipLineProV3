import React, { useState, useEffect } from 'react';
import { Bell, X, TrendingUp, TrendingDown, DollarSign, AlertTriangle, Info } from 'lucide-react';
import { api } from '../utils/apiClient';

interface RateNotification {
  id: string;
  type: 'increase' | 'decrease' | 'volatility' | 'info';
  title: string;
  message: string;
  currentRate: number;
  previousRate: number;
  changePercent: number;
  timestamp: string;
  isRead: boolean;
}

interface ExchangeRateNotificationsProps {
  onNotificationCount?: (count: number) => void;
}

const ExchangeRateNotifications: React.FC<ExchangeRateNotificationsProps> = ({
  onNotificationCount,
}) => {
  const [notifications, setNotifications] = useState<RateNotification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  // Fetch rate notifications
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      
      const response = await api.get('/exchange-rates/notifications');
      const data = await api.parseResponse(response);
      
      if (response.ok && data.notifications) {
        setNotifications(data.notifications);
        
        // Update notification count for parent component
        const unreadCount = data.notifications.filter((n: RateNotification) => !n.isRead).length;
        if (onNotificationCount) {
          onNotificationCount(unreadCount);
        }
      }
    } catch (error) {
      console.error('Error fetching rate notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mark notification as read
  const markAsRead = async (notificationId: string) => {
    try {
      await api.put(`/api/v1/exchange-rates/notifications/${notificationId}/read`);
      
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, isRead: true } : n)
      );
      
      // Update unread count
      const unreadCount = notifications.filter(n => n.id !== notificationId && !n.isRead).length;
      if (onNotificationCount) {
        onNotificationCount(unreadCount);
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      await api.put('/api/v1/exchange-rates/notifications/read-all');
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, isRead: true }))
      );
      
      if (onNotificationCount) {
        onNotificationCount(0);
      }
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // Dismiss notification
  const dismissNotification = async (notificationId: string) => {
    try {
      await api.delete(`/api/v1/exchange-rates/notifications/${notificationId}`);
      
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      
      // Update unread count
      const notification = notifications.find(n => n.id === notificationId);
      if (notification && !notification.isRead && onNotificationCount) {
        const unreadCount = notifications.filter(n => n.id !== notificationId && !n.isRead).length;
        onNotificationCount(unreadCount);
      }
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
  };

  // Fetch notifications on component mount and set up periodic refresh
  useEffect(() => {
    fetchNotifications();
    
    // Set up periodic refresh every 5 minutes
    const interval = setInterval(fetchNotifications, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'increase':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'decrease':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      case 'volatility':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      default:
        return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  const getNotificationColor = (type: string, isRead: boolean) => {
    const opacity = isRead ? 'opacity-60' : '';
    
    switch (type) {
      case 'increase':
        return `bg-green-50 border-green-200 ${opacity}`;
      case 'decrease':
        return `bg-red-50 border-red-200 ${opacity}`;
      case 'volatility':
        return `bg-yellow-50 border-yellow-200 ${opacity}`;
      default:
        return `bg-gray-50 border-gray-200 ${opacity}`;
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      month: 'short',
      day: 'numeric',
    });
  };

  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <div className="relative">
      {/* Notification Bell Button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      {showDropdown && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-hidden">
          {/* Header */}
          <div className="border-b border-gray-100 px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5 text-gray-600" />
                <h3 className="text-sm font-semibold text-gray-900">Exchange Rate Alerts</h3>
                {unreadCount > 0 && (
                  <span className="bg-red-100 text-red-700 text-xs px-2 py-1 rounded-full">
                    {unreadCount} new
                  </span>
                )}
              </div>
              <button
                onClick={() => setShowDropdown(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-xs text-gray-600 hover:text-gray-800 mt-2 transition-colors"
              >
                Mark all as read
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-600"></div>
                <span className="ml-2 text-sm text-gray-600">Loading...</span>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-gray-500">
                <Bell className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No exchange rate alerts</p>
                <p className="text-xs">You'll be notified of significant rate changes</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                      !notification.isRead ? 'bg-gray-50/30' : ''
                    }`}
                    onClick={() => !notification.isRead && markAsRead(notification.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        {getNotificationIcon(notification.type)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <h4 className={`text-sm font-medium ${
                              !notification.isRead ? 'text-gray-900' : 'text-gray-600'
                            }`}>
                              {notification.title}
                            </h4>
                            <time className="text-xs text-gray-500">
                              {formatTime(notification.timestamp)}
                            </time>
                          </div>
                          
                          <p className={`text-sm mt-1 ${
                            !notification.isRead ? 'text-gray-700' : 'text-gray-500'
                          }`}>
                            {notification.message}
                          </p>
                          
                          <div className="flex items-center justify-between mt-2">
                            <div className="flex items-center space-x-4 text-xs">
                              <span className="text-gray-600">
                                Current: ₺{notification.currentRate.toFixed(4)}
                              </span>
                              <span className={`font-medium ${
                                notification.changePercent > 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {notification.changePercent > 0 ? '+' : ''}{notification.changePercent.toFixed(2)}%
                              </span>
                            </div>
                            
                            {!notification.isRead && (
                              <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          dismissNotification(notification.id);
                        }}
                        className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="border-t border-gray-100 px-4 py-3 bg-gray-50">
              <div className="text-center">
                <button
                  onClick={fetchNotifications}
                  className="text-xs text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Refresh notifications
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Click outside to close */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};

export default ExchangeRateNotifications;
