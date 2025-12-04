import React from 'react';
import { CheckCircle, AlertCircle, Clock, Wifi, WifiOff, Database, RefreshCw } from 'lucide-react';

export type StatusType = 'online' | 'offline' | 'loading' | 'success' | 'warning' | 'error' | 'syncing' | 'idle';

interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  showIcon?: boolean;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  className?: string;
}

/**
 * StatusIndicator Component - Shows system/data status with minimal icons
 * 
 * Features:
 * - Multiple status types (online, offline, loading, etc.)
 * - Optional pulse animation
 * - Minimal design with small colored dots
 * - Optional text label
 * - Accessible with proper aria labels
 * 
 * Usage:
 * <StatusIndicator status="online" label="Live Data" pulse />
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  showIcon = false,
  showLabel = true,
  size = 'md',
  pulse = false,
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const iconSizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };

  const statusConfig = {
    online: {
      color: 'bg-green-500',
      textColor: 'text-green-700',
      icon: Wifi,
      label: label || 'Online',
      ariaLabel: 'System is online'
    },
    offline: {
      color: 'bg-gray-400',
      textColor: 'text-gray-600',
      icon: WifiOff,
      label: label || 'Offline',
      ariaLabel: 'System is offline'
    },
    loading: {
      color: 'bg-blue-500',
      textColor: 'text-blue-700',
      icon: RefreshCw,
      label: label || 'Loading',
      ariaLabel: 'Loading data',
      iconClass: 'animate-spin'
    },
    success: {
      color: 'bg-green-500',
      textColor: 'text-green-700',
      icon: CheckCircle,
      label: label || 'Success',
      ariaLabel: 'Operation successful'
    },
    warning: {
      color: 'bg-amber-500',
      textColor: 'text-amber-700',
      icon: AlertCircle,
      label: label || 'Warning',
      ariaLabel: 'Warning state'
    },
    error: {
      color: 'bg-red-500',
      textColor: 'text-red-700',
      icon: AlertCircle,
      label: label || 'Error',
      ariaLabel: 'Error state'
    },
    syncing: {
      color: 'bg-blue-500',
      textColor: 'text-blue-700',
      icon: Database,
      label: label || 'Syncing',
      ariaLabel: 'Syncing data',
      iconClass: 'animate-pulse'
    },
    idle: {
      color: 'bg-gray-300',
      textColor: 'text-gray-600',
      icon: Clock,
      label: label || 'Idle',
      ariaLabel: 'System idle'
    }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div 
      className={`inline-flex items-center gap-2 ${className}`}
      role="status"
      aria-label={config.ariaLabel}
    >
      {showIcon ? (
        <Icon 
          className={`${iconSizeClasses[size]} ${config.textColor} ${config.iconClass || ''}`}
          aria-hidden="true"
        />
      ) : (
        <span 
          className={`
            ${sizeClasses[size]} 
            ${config.color} 
            rounded-full 
            flex-shrink-0
            ${pulse ? 'animate-status-pulse' : ''}
          `}
          aria-hidden="true"
        />
      )}
      {showLabel && (
        <span className={`${textSizeClasses[size]} ${config.textColor} font-medium`}>
          {config.label}
        </span>
      )}
    </div>
  );
};

/**
 * DataFreshnessIndicator - Shows how fresh the data is
 */
interface DataFreshnessProps {
  lastUpdated: Date | string;
  className?: string;
}

export const DataFreshnessIndicator: React.FC<DataFreshnessProps> = ({ 
  lastUpdated, 
  className = '' 
}) => {
  const getStatus = (): StatusType => {
    const date = typeof lastUpdated === 'string' ? new Date(lastUpdated) : lastUpdated;
    const now = new Date();
    const diffMinutes = (now.getTime() - date.getTime()) / (1000 * 60);

    if (diffMinutes < 1) return 'online';
    if (diffMinutes < 5) return 'success';
    if (diffMinutes < 30) return 'warning';
    return 'error';
  };

  const getTimeAgo = (): string => {
    const date = typeof lastUpdated === 'string' ? new Date(lastUpdated) : lastUpdated;
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSeconds < 60) return 'Just now';
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
    return `${Math.floor(diffSeconds / 86400)}d ago`;
  };

  return (
    <StatusIndicator 
      status={getStatus()}
      label={getTimeAgo()}
      size="sm"
      pulse={getStatus() === 'online'}
      className={className}
    />
  );
};

export default StatusIndicator;

