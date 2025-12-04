/**
 * Unified Notification System - Export File
 * Single entry point for notification components and hooks
 */

export { 
  NotificationContainer,
  useUnifiedNotifications,
  type UnifiedNotification,
  type NotificationType,
  type NotificationPosition
} from './UnifiedNotification';

export { 
  NotificationProvider,
  useNotifications,
  useNotification  // Alias for compatibility
} from '../../contexts/NotificationContext';

export { NotificationExamples } from './NotificationExamples';

