import React from 'react';
import { AlertCircle, RefreshCw, AlertTriangle } from 'lucide-react';
import { UnifiedButton } from '../../design-system';
import { useLanguage } from '../../contexts/LanguageContext';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  variant?: 'error' | 'warning' | 'info';
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  onRetry,
  retryLabel,
  variant = 'error',
  className = '',
}) => {
  const { t } = useLanguage();

  const defaultTitle = variant === 'error' 
    ? t('common.error_occurred') || 'An error occurred'
    : variant === 'warning'
    ? t('common.warning') || 'Warning'
    : t('common.info') || 'Information';

  const defaultMessage = variant === 'error'
    ? t('common.error_loading_data') || 'Failed to load data. Please try again.'
    : message || '';

  const iconColor = variant === 'error' 
    ? 'text-red-600' 
    : variant === 'warning'
    ? 'text-yellow-600'
    : 'text-blue-600';

  const bgColor = variant === 'error'
    ? 'bg-red-50 border-red-200'
    : variant === 'warning'
    ? 'bg-yellow-50 border-yellow-200'
    : 'bg-blue-50 border-blue-200';

  const Icon = variant === 'warning' ? AlertTriangle : AlertCircle;

  return (
    <div className={`rounded-xl border p-6 ${bgColor} ${className}`}>
      <div className="flex flex-col items-center text-center">
        <div className={`w-12 h-12 ${iconColor} mb-4`}>
          <Icon className="h-12 w-12" />
        </div>
        <h3 className={`text-lg font-semibold mb-2 ${
          variant === 'error' ? 'text-red-800' : 
          variant === 'warning' ? 'text-yellow-800' : 
          'text-blue-800'
        }`}>
          {title || defaultTitle}
        </h3>
        <p className={`text-sm mb-4 ${
          variant === 'error' ? 'text-red-700' : 
          variant === 'warning' ? 'text-yellow-700' : 
          'text-blue-700'
        }`}>
          {message || defaultMessage}
        </p>
        {onRetry && (
          <UnifiedButton
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            {retryLabel || t('common.retry') || 'Retry'}
          </UnifiedButton>
        )}
      </div>
    </div>
  );
};

