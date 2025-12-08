/**
 * Custom Hook: useNotifications
 * Real-time notifications management
 */

import { useState, useEffect, useCallback } from 'react';
import { logger } from '../utils/logger';
import { apiClient } from '../utils/apiClient';

export interface Notification {
  id: number;
  type: 'info' | 'warning' | 'success' | 'error';
  title: string;
  message: string;
  time: string;
  read: boolean;
  createdAt: string;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  refresh: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

export const useNotifications = (): UseNotificationsReturn => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Try to fetch from API
      const response = await apiClient.get<{ notifications: Notification[] }>('/notifications', {
        timeout: 5000,
        retries: 1,
      });

      setNotifications(response.data.notifications || []);
    } catch (err: any) {
      // 404 is expected if endpoint doesn't exist - silent fail
      if (err.message?.includes('404') || err.message?.includes('bulunamadı')) {
        setNotifications([]);
        setError(null);
        return;
      }
      
      logger.warn('Failed to load notifications from API, using fallback', err);
      
      // Fallback: Empty notifications (or could use localStorage)
      setNotifications([]);
      setError(null); // Don't show error for notifications
    } finally {
      setLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (id: number) => {
    try {
      await apiClient.post(`/notifications/${id}/read`, {});
      
      setNotifications((prev) =>
        prev.map((notif) => (notif.id === id ? { ...notif, read: true } : notif)),
      );
    } catch (err) {
      logger.error('Failed to mark notification as read', err);
      // Optimistic update even if API fails
      setNotifications((prev) =>
        prev.map((notif) => (notif.id === id ? { ...notif, read: true } : notif)),
      );
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await apiClient.post('/notifications/read-all', {});
      
      setNotifications((prev) => prev.map((notif) => ({ ...notif, read: true })));
    } catch (err) {
      logger.error('Failed to mark all notifications as read', err);
      // Optimistic update
      setNotifications((prev) => prev.map((notif) => ({ ...notif, read: true })));
    }
  }, []);

  useEffect(() => {
    loadNotifications();

    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      loadNotifications();
    }, 30000);

    return () => clearInterval(interval);
  }, [loadNotifications]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    refresh: loadNotifications,
    loading,
    error,
  };
};
