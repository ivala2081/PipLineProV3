/**
 * Unified Notification Context
 * Provides notification functionality throughout the application
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { 
  NotificationContainer, 
  useUnifiedNotifications,
  UnifiedNotification,
  NotificationPosition
} from '../components/notifications/UnifiedNotification';

interface NotificationContextType {
  notifications: UnifiedNotification[];
  success: (title: string, message?: string, options?: Partial<UnifiedNotification>) => string;
  error: (title: string, message?: string, options?: Partial<UnifiedNotification>) => string;
  warning: (title: string, message?: string, options?: Partial<UnifiedNotification>) => string;
  info: (title: string, message?: string, options?: Partial<UnifiedNotification>) => string;
  addNotification: (notification: Omit<UnifiedNotification, 'id'>) => string;
  dismissNotification: (id: string) => void;
  dismissAll: () => void;
  addUnique: (key: string, notification: Omit<UnifiedNotification, 'id'>) => string | null;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
  position?: NotificationPosition;
  maxVisible?: number;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ 
  children, 
  position = 'top-right',
  maxVisible = 5
}) => {
  const notificationMethods = useUnifiedNotifications();

  return (
    <NotificationContext.Provider value={notificationMethods}>
      {children}
      <NotificationContainer
        notifications={notificationMethods.notifications}
        onDismiss={notificationMethods.dismissNotification}
        position={position}
        maxVisible={maxVisible}
      />
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

// Export for backwards compatibility
export { useNotifications as useNotification };

