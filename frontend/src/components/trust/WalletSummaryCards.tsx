import React from 'react';
import { Wallet, Activity, DollarSign, Shield, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui';
import { useLanguage } from '../../contexts/LanguageContext';

interface TrustSummary {
  overall: {
    total_wallets: number;
    total_transactions: number;
    total_amount_try: number;
    active_networks: number;
  };
  by_network: Array<{
    network: string;
    wallet_count: number;
    transaction_count: number;
    total_amount_try: number;
  }>;
  recent_activity: {
    last_24h_transactions: number;
    last_24h_amount_try: number;
    growth_percentage: number;
  };
}

interface WalletSummaryCardsProps {
  summary: TrustSummary | null;
  loading?: boolean;
}

const WalletSummaryCards: React.FC<WalletSummaryCardsProps> = ({
  summary,
  loading = false
}) => {
  const { t } = useLanguage();

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {[...Array(4)].map((_, index) => (
          <Card key={index} className="animate-pulse">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                  <div className="h-8 bg-gray-200 rounded w-16"></div>
                </div>
                <div className="h-8 w-8 bg-gray-200 rounded"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Wallets</p>
                <p className="text-2xl font-bold text-gray-900">0</p>
              </div>
              <Wallet className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{t('trust_wallet.total_transactions')}</p>
                <p className="text-2xl font-bold text-gray-900">0</p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{t('trust_wallet.total_value_try')}</p>
                <p className="text-2xl font-bold text-gray-900">₺0</p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{t('trust_wallet.active_networks')}</p>
                <p className="text-2xl font-bold text-gray-900">0</p>
              </div>
              <Shield className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('tr-TR').format(num);
  };

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) {
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    } else if (growth < 0) {
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    }
    return null;
  };

  const getGrowthColor = (growth: number) => {
    if (growth > 0) return 'text-green-600';
    if (growth < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-6 mb-6">
      {/* Main Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="hover:shadow-md transition-shadow duration-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Wallets</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatNumber(summary.overall.total_wallets)}
                </p>
              </div>
              <Wallet className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow duration-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Transactions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatNumber(summary.overall.total_transactions)}
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow duration-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Value (TRY)</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(summary.overall.total_amount_try)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow duration-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Networks</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.overall.active_networks}
                </p>
              </div>
              <Shield className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Card */}
      <Card className="hover:shadow-md transition-shadow duration-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            {t('trust_wallet.recent_activity_24h')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">{t('trust_wallet.transactions')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatNumber(summary.recent_activity.last_24h_transactions)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">{t('trust_wallet.volume_try', 'Volume (TRY)')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary.recent_activity.last_24h_amount_try)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600">{t('trust_wallet.growth', 'Growth')}</p>
              <div className="flex items-center justify-center gap-1">
                {getGrowthIcon(summary.recent_activity.growth_percentage)}
                <p className={`text-2xl font-bold ${getGrowthColor(summary.recent_activity.growth_percentage)}`}>
                  {summary.recent_activity.growth_percentage > 0 ? '+' : ''}
                  {summary.recent_activity.growth_percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Network Breakdown */}
      {summary.by_network && summary.by_network.length > 0 && (
        <Card className="hover:shadow-md transition-shadow duration-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-purple-600" />
              {t('trust_wallet.network_breakdown')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {summary.by_network.map((network) => (
                <div key={network.network} className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-center mb-2">
                    <div className={`h-3 w-3 rounded-full mr-2 ${
                      network.network === 'ETH' ? 'bg-blue-500' :
                      network.network === 'BSC' ? 'bg-yellow-500' :
                      network.network === 'TRC' ? 'bg-red-500' : 'bg-gray-500'
                    }`} />
                    <span className="font-semibold text-gray-900">{network.network}</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-1">
                    {formatNumber(network.wallet_count)} {t('trust_wallet.wallets')}
                  </p>
                  <p className="text-sm text-gray-600 mb-1">
                    {formatNumber(network.transaction_count)} {t('trust_wallet.transactions')}
                  </p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(network.total_amount_try)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WalletSummaryCards;
