import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  CreditCard, 
  Users, 
  BarChart3, 
  RefreshCw, 
  FileText, 
  PieChart, 
  Settings, 
  Activity 
} from 'lucide-react';
import { UnifiedSection } from '../../design-system/UnifiedSection';
import { UnifiedGrid } from '../../design-system/UnifiedGrid';
import { UnifiedButton } from '../../design-system/UnifiedButton';

interface DashboardQuickActionsProps {
  onQuickAction: (title: string, path: string) => void;
  onRefresh: () => void;
  refreshing: boolean;
}

export const DashboardQuickActions: React.FC<DashboardQuickActionsProps> = ({
  onQuickAction,
  onRefresh,
  refreshing
}) => {
  const { t } = useTranslation();

  return (
    <UnifiedSection title={t('dashboard.quick_actions')} description={t('dashboard.common_tasks_shortcuts')}>
      <UnifiedGrid cols={4} gap="lg">
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-gray-50 hover:border-gray-200 transition-colors"
          onClick={() => onQuickAction(t('dashboard.add_transaction'), '/transactions/add')}
        >
          <CreditCard className="h-6 w-6 text-gray-600" />
          <span className="text-sm font-medium">{t('dashboard.add_transaction')}</span>
        </UnifiedButton>
        
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-green-50 hover:border-green-200 transition-colors"
          onClick={() => onQuickAction(t('dashboard.manage_clients'), '/clients')}
        >
          <Users className="h-6 w-6 text-green-600" />
          <span className="text-sm font-medium">{t('dashboard.manage_clients')}</span>
        </UnifiedButton>
        
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-purple-50 hover:border-purple-200 transition-colors"
          onClick={() => onQuickAction(t('dashboard.view_analytics'), '/analytics')}
        >
          <BarChart3 className="h-6 w-6 text-purple-600" />
          <span className="text-sm font-medium">{t('dashboard.view_analytics')}</span>
        </UnifiedButton>
        
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-orange-50 hover:border-orange-200 transition-colors"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw className={`h-6 w-6 text-orange-600 ${refreshing ? 'animate-spin' : ''}`} />
          <span className="text-sm font-medium">{refreshing ? t('common.refreshing') : t('dashboard.refresh_data')}</span>
        </UnifiedButton>
      </UnifiedGrid>
      
      {/* Additional Quick Actions Row */}
      <UnifiedGrid cols={4} gap="lg" className="mt-4">
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-indigo-50 hover:border-indigo-200 transition-colors"
          onClick={() => onQuickAction(t('dashboard.view_transactions'), '/transactions')}
        >
          <FileText className="h-6 w-6 text-indigo-600" />
          <span className="text-sm font-medium">{t('dashboard.view_transactions')}</span>
        </UnifiedButton>
        
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-teal-50 hover:border-teal-200 transition-colors"
          onClick={() => onQuickAction(t('dashboard.generate_reports'), '/reports')}
        >
          <PieChart className="h-6 w-6 text-teal-600" />
          <span className="text-sm font-medium">{t('dashboard.generate_reports')}</span>
        </UnifiedButton>
        
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-rose-50 hover:border-rose-200 transition-colors"
          onClick={() => onQuickAction(t('common.settings'), '/settings')}
        >
          <Settings className="h-6 w-6 text-rose-600" />
          <span className="text-sm font-medium">{t('common.settings')}</span>
        </UnifiedButton>
        
        <UnifiedButton
          variant="outline"
          className="h-24 flex flex-col items-center justify-center gap-2 hover:bg-amber-50 hover:border-amber-200 transition-colors"
          onClick={() => onQuickAction(t('dashboard.system_monitor'), '/system-monitor')}
        >
          <Activity className="h-6 w-6 text-amber-600" />
          <span className="text-sm font-medium">{t('dashboard.system_monitor')}</span>
        </UnifiedButton>
      </UnifiedGrid>
    </UnifiedSection>
  );
};
