import React from 'react';
import { Button } from '../ui/button';
import { Download, Filter, RefreshCw, Settings } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

interface QuickActionBarProps {
  onExport?: () => void;
  onFilter?: () => void;
  onRefresh?: () => void;
  onSettings?: () => void;
  refreshing?: boolean;
  isGeneratingReport?: boolean;
}

export const QuickActionBar: React.FC<QuickActionBarProps> = ({
  onExport,
  onFilter,
  onRefresh,
  onSettings,
  refreshing = false,
  isGeneratingReport = false,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex items-center gap-2">
      {/* Filter Button */}
      {onFilter && (
        <Button
          variant="outline"
          size="sm"
          onClick={onFilter}
          className="h-9 px-3 bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-900 transition-all duration-200"
        >
          <Filter className="w-4 h-4 mr-2" />
          {t('common.filter') || 'Filter'}
        </Button>
      )}

      {/* Export Button */}
      {onExport && (
        <Button
          variant="outline"
          size="sm"
          onClick={onExport}
          disabled={isGeneratingReport}
          className="h-9 px-3 bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-900 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className={`w-4 h-4 mr-2 ${isGeneratingReport ? 'animate-pulse' : ''}`} />
          {isGeneratingReport 
            ? (t('common.loading') || 'Generating...') 
            : (t('clients.export') || 'Export')
          }
        </Button>
      )}

      {/* Refresh Button */}
      {onRefresh && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={refreshing}
          className="h-9 px-3 bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-900 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {t('common.refresh') || 'Refresh'}
        </Button>
      )}

      {/* Settings Button */}
      {onSettings && (
        <Button
          variant="outline"
          size="sm"
          onClick={onSettings}
          className="h-9 px-3 bg-white border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-900 transition-all duration-200"
        >
          <Settings className="w-4 h-4 mr-2" />
          {t('common.settings') || 'Settings'}
        </Button>
      )}
    </div>
  );
};

export default QuickActionBar;

