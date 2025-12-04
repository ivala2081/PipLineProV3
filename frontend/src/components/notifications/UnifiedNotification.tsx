/**
 * Unified Notification System - Professional & Business-Oriented
 * Single source of truth for all notifications in the application
 */

import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, AlertCircle, Info, X, AlertTriangle } from 'lucide-react';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';
export type NotificationPosition = 'top-right' | 'top-center' | 'bottom-right';

export interface UnifiedNotification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  dismissible?: boolean;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationProps {
  notification: UnifiedNotification;
  onDismiss: (id: string) => void;
  position: NotificationPosition;
}

const NotificationComponent: React.FC<NotificationProps> = ({ 
  notification, 
  onDismiss,
  position 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (notification.duration && notification.duration > 0 && !notification.persistent) {
      const startTime = Date.now();
      const endTime = startTime + notification.duration;
      
      const progressTimer = setInterval(() => {
        const now = Date.now();
        const remaining = endTime - now;
        const newProgress = Math.max(0, (remaining / (notification.duration || 5000)) * 100);
        setProgress(newProgress);
        
        if (remaining <= 0) {
          clearInterval(progressTimer);
          handleDismiss();
        }
      }, 50);

      return () => clearInterval(progressTimer);
    }
    return undefined;
  }, [notification.duration, notification.persistent]);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss(notification.id);
    }, 300);
  }, [notification.id, onDismiss]);

  const getIcon = () => {
    const iconClass = "w-5 h-5 flex-shrink-0";
    switch (notification.type) {
      case 'success':
        return <CheckCircle className={`${iconClass} text-green-700`} />;
      case 'error':
        return <AlertCircle className={`${iconClass} text-red-700`} />;
      case 'warning':
        return <AlertTriangle className={`${iconClass} text-amber-700`} />;
      case 'info':
        return <Info className={`${iconClass} text-blue-700`} />;
    }
  };

  const getTypeStyles = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-white border-l-4 border-l-green-600 shadow-lg';
      case 'error':
        return 'bg-white border-l-4 border-l-red-600 shadow-lg';
      case 'warning':
        return 'bg-white border-l-4 border-l-amber-600 shadow-lg';
      case 'info':
        return 'bg-white border-l-4 border-l-blue-600 shadow-lg';
    }
  };

  const getProgressColor = () => {
    switch (notification.type) {
      case 'success': return 'bg-green-600';
      case 'error': return 'bg-red-600';
      case 'warning': return 'bg-amber-600';
      case 'info': return 'bg-blue-600';
    }
  };

  const baseClasses = `
    relative w-full max-w-md rounded-lg border border-gray-200
    ${getTypeStyles()}
    transition-all duration-300 ease-in-out
  `;

  const animationClasses = isExiting
    ? 'translate-x-full opacity-0'
    : isVisible
    ? 'translate-x-0 opacity-100'
    : 'translate-x-full opacity-0';

  return (
    <div className={`${baseClasses} ${animationClasses} mb-3`}>
      <div className="flex items-start gap-3 p-4">
        {getIcon()}
        
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 leading-tight">
            {notification.title}
          </h4>
          {notification.message && (
            <p className="mt-1 text-sm text-gray-600 leading-snug">
              {notification.message}
            </p>
          )}
          {notification.action && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                notification.action?.onClick();
                handleDismiss();
              }}
              className="mt-2 text-sm font-medium text-gray-900 hover:text-gray-700 underline transition-colors"
            >
              {notification.action.label}
            </button>
          )}
        </div>
        
        {notification.dismissible !== false && (
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors p-1 rounded hover:bg-gray-100"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {notification.duration && !notification.persistent && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100 rounded-b-lg overflow-hidden">
          <div 
            className={`h-full ${getProgressColor()} transition-all duration-100 ease-linear`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

// Container Component
interface NotificationContainerProps {
  notifications: UnifiedNotification[];
  onDismiss: (id: string) => void;
  position?: NotificationPosition;
  maxVisible?: number;
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({ 
  notifications, 
  onDismiss, 
  position = 'top-right',
  maxVisible = 5
}) => {
  const getPositionClasses = () => {
    switch (position) {
      case 'top-right':
        return 'fixed top-4 right-4 z-50 flex flex-col items-end';
      case 'top-center':
        return 'fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center';
      case 'bottom-right':
        return 'fixed bottom-4 right-4 z-50 flex flex-col items-end';
    }
  };

  const visibleNotifications = notifications.slice(0, maxVisible);

  if (visibleNotifications.length === 0) return null;

  return (
    <div className={getPositionClasses()}>
      {visibleNotifications.map((notification) => (
        <NotificationComponent
          key={notification.id}
          notification={notification}
          onDismiss={onDismiss}
          position={position}
        />
      ))}
      {notifications.length > maxVisible && (
        <div className="text-sm text-gray-500 text-center mt-2">
          +{notifications.length - maxVisible} more notifications
        </div>
      )}
    </div>
  );
};

// Hook for managing notifications
export const useUnifiedNotifications = () => {
  const [notifications, setNotifications] = useState<UnifiedNotification[]>([]);

  const addNotification = useCallback((notification: Omit<UnifiedNotification, 'id'>) => {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: UnifiedNotification = {
      id,
      duration: 5000,
      dismissible: true,
      persistent: false,
      ...notification
    };

    setNotifications(prev => [...prev, newNotification]);
    return id;
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Convenience methods
  const success = useCallback((title: string, message?: string, options?: Partial<UnifiedNotification>) => {
    return addNotification({ type: 'success', title, message, ...options });
  }, [addNotification]);

  const error = useCallback((title: string, message?: string, options?: Partial<UnifiedNotification>) => {
    return addNotification({ 
      type: 'error', 
      title, 
      message, 
      duration: 8000,
      ...options 
    });
  }, [addNotification]);

  const warning = useCallback((title: string, message?: string, options?: Partial<UnifiedNotification>) => {
    return addNotification({ 
      type: 'warning', 
      title, 
      message, 
      duration: 6000,
      ...options 
    });
  }, [addNotification]);

  const info = useCallback((title: string, message?: string, options?: Partial<UnifiedNotification>) => {
    return addNotification({ type: 'info', title, message, ...options });
  }, [addNotification]);

  // Prevent duplicate notifications
  const addUnique = useCallback((
    key: string,
    notification: Omit<UnifiedNotification, 'id'>
  ) => {
    // Check if a notification with this key already exists
    const exists = notifications.some(n => n.id.includes(key));
    if (!exists) {
      return addNotification(notification);
    }
    return null;
  }, [notifications, addNotification]);

  return {
    notifications,
    addNotification,
    dismissNotification,
    dismissAll,
    success,
    error,
    warning,
    info,
    addUnique
  };
};

