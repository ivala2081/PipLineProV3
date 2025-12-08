/**
 * Deprecation Notice for Old Notification Systems
 * This file marks deprecated notification components
 */

/* 
 * DEPRECATED COMPONENTS - DO NOT USE
 * ================================
 * 
 * The following components are deprecated and should not be used in new code:
 * 
 * 1. components/Toast.tsx - Use UnifiedNotification instead
 * 2. components/ui/notification.tsx - Use UnifiedNotification instead
 * 3. hooks/useToast.ts - Use useNotifications hook instead
 * 4. hooks/useUniqueToast.ts - Use useNotifications().addUnique() instead
 * 
 * MIGRATION GUIDE
 * ==============
 * 
 * OLD (Toast.tsx):
 * ```tsx
 * import { useToast } from './components/Toast';
 * const { showSuccess, showError } = useToast();
 * showSuccess('Title', 'Message');
 * ```
 * 
 * NEW (UnifiedNotification):
 * ```tsx
 * import { useNotifications } from '@/hooks/useNotifications';
 * const { success, error } = useNotifications();
 * success('Title', 'Message');
 * ```
 * 
 * EXCEPTIONS
 * ==========
 * 
 * Keep these components (special purpose):
 * - components/ExchangeRateNotifications.tsx (bell icon dropdown)
 * - components/modern/NotificationSystem.tsx (system notifications dropdown)
 * 
 * These serve different purposes than toast notifications.
 * 
 * For more information, see:
 * frontend/src/components/notifications/README.md
 */

export const DEPRECATED_MESSAGE = `
This component is deprecated. Please use the Unified Notification System instead.
See: frontend/src/components/notifications/README.md
`;

console.warn(DEPRECATED_MESSAGE);

