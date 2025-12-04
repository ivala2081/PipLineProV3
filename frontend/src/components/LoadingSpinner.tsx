import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'neutral';
  message?: string;
  className?: string;
  fullScreen?: boolean;
  showDots?: boolean;
  showBar?: boolean;
  indeterminate?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'default',
  message = 'Loading...',
  className = '',
  fullScreen = false,
  showDots = false,
  showBar = false,
  indeterminate = false
}) => {
  const sizeClasses = {
    sm: 'business-loading-spinner-sm',
    md: 'business-loading-spinner-md',
    lg: 'business-loading-spinner-lg',
    xl: 'business-loading-spinner-xl'
  };

  const variantClasses = {
    default: 'business-loading-spinner',
    primary: 'business-loading-spinner-primary',
    success: 'business-loading-spinner-success',
    warning: 'business-loading-spinner-warning',
    error: 'business-loading-spinner-error',
    neutral: 'business-loading-spinner-neutral'
  };

  const containerClasses = fullScreen 
    ? 'business-loading-overlay'
    : 'flex items-center justify-center';

  const getSpinnerClasses = () => {
    if (showDots) {
      return `business-loading-dots business-loading-dots-${variant}`;
    }
    if (showBar) {
      return `business-loading-bar business-loading-bar-${indeterminate ? 'indeterminate' : variant}`;
    }
    return `${sizeClasses[size]} ${variantClasses[variant]}`;
  };

  const renderSpinner = () => {
    if (showDots) {
      return (
        <div className="business-loading-dots business-loading-dots-primary">
          <div className="business-loading-dots-dot"></div>
          <div className="business-loading-dots-dot"></div>
          <div className="business-loading-dots-dot"></div>
        </div>
      );
    }

    if (showBar) {
      return (
        <div className="business-loading-bar">
          <div className="business-loading-bar-progress"></div>
        </div>
      );
    }

    return (
      <div 
        className={getSpinnerClasses()}
        aria-hidden="true"
      />
    );
  };

  return (
    <div 
      className={`${containerClasses} ${className}`}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="flex flex-col items-center gap-3">
        {renderSpinner()}
        {message && (
          <p className="text-sm text-gray-600 font-medium" aria-live="polite">
            {message}
          </p>
        )}
      </div>
    </div>
  );
};

export default LoadingSpinner;
