/**
 * Backend Status Notification Component
 * Kullaniciyi backend restart/downtime durumunda bilgilendirir
 */

import React, { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface BackendStatusNotificationProps {
  isBackendDown: boolean;
  onRetry?: () => void;
}

export const BackendStatusNotification: React.FC<BackendStatusNotificationProps> = ({
  isBackendDown,
  onRetry
}) => {
  const [show, setShow] = useState(false);
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    if (isBackendDown) {
      setShow(true);
      // Start countdown for auto-retry
      const interval = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            if (onRetry) onRetry();
            return 5;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    } else {
      // Backend is back online
      if (show) {
        // Show success message briefly
        setTimeout(() => setShow(false), 3000);
      }
    }
  }, [isBackendDown, show, onRetry]);

  if (!show) return null;

  return (
    <div className="fixed top-4 right-4 z-[9999] max-w-md animate-in slide-in-from-top duration-300">
      {isBackendDown ? (
        <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg shadow-xl p-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <RefreshCw className="w-5 h-5 text-amber-600 animate-spin" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-amber-900 mb-1">
                System Update in Progress
              </h3>
              <p className="text-xs text-amber-800 mb-2">
                The backend is currently restarting. Your requests will be automatically retried.
              </p>
              <div className="flex items-center gap-2">
                <div className="h-1 flex-1 bg-amber-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-amber-600 transition-all duration-1000 ease-linear"
                    style={{ width: `${(5 - countdown) * 20}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-amber-700">
                  {countdown}s
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-green-50 border-l-4 border-green-500 rounded-lg shadow-xl p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <div>
              <h3 className="text-sm font-semibold text-green-900">
                System Online
              </h3>
              <p className="text-xs text-green-800">
                Backend is back online. Processing queued requests...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

