import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, FileText, BarChart3, Users } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import MetricCard from '../MetricCard';
import { formatCurrency } from '../../utils/currencyUtils';

interface ClientsOverviewTabProps {
  dashboardFinancialData: any;
  totalDeposits: number;
  totalWithdrawals: number;
  totalCommissions: number;
  loading: boolean;
}

export const ClientsOverviewTab: React.FC<ClientsOverviewTabProps> = ({
  dashboardFinancialData,
  totalDeposits,
  totalWithdrawals,
  totalCommissions,
  loading,
}) => {
  const { t } = useLanguage();

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div className="mt-6">
      {/* Professional Financial Metrics Section */}
      <div className="mb-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-gray-600" />
            {t('clients.financial_overview')}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {t('clients.key_financial_metrics')}
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title={t('ledger.total_deposits')}
            value={formatCurrency(dashboardFinancialData?.total_deposits || totalDeposits, '₺')}
            subtitle={t('clients.all_dep_transactions')}
            icon={TrendingUp}
            color="green"
            animated={true}
            animationDuration={500}
            showGlass={true}
          />
          
          <MetricCard
            title={t('ledger.total_withdrawals')}
            value={formatCurrency(Math.abs(dashboardFinancialData?.total_withdrawals || totalWithdrawals), '₺')}
            subtitle={t('clients.all_wd_transactions')}
            icon={TrendingDown}
            color="red"
            animated={true}
            animationDuration={500}
            showGlass={true}
          />
          
          <MetricCard
            title={t('dashboard.net_cash')}
            value={formatCurrency((dashboardFinancialData?.total_deposits || totalDeposits) - (dashboardFinancialData?.total_withdrawals || totalWithdrawals), '₺')}
            subtitle={t('clients.all_transactions_net')}
            icon={DollarSign}
            color={((dashboardFinancialData?.total_deposits || totalDeposits) - (dashboardFinancialData?.total_withdrawals || totalWithdrawals)) >= 0 ? "gray" : "red"}
            animated={true}
            animationDuration={500}
          />
          
          <MetricCard
            title={t('dashboard.total_commissions')}
            value={formatCurrency(dashboardFinancialData?.total_commission || totalCommissions, '₺')}
            subtitle={t('clients.all_transactions_commission')}
            icon={FileText}
            color="purple"
            animated={true}
            animationDuration={500}
          />
        </div>
      </div>

      {/* Client Distribution and Top Performers Section */}
      <div className="mb-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Users className="h-5 w-5 text-gray-600" />
            {t('clients.client_insights')}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {t('clients.distribution_top_performers')}
          </p>
        </div>
        {/* Additional charts and visualizations will go here */}
      </div>
    </div>
  );
};

