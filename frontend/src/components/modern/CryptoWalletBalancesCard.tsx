import React, { useState, useEffect, useCallback } from 'react';
import { Wallet, RefreshCw } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { StatusIndicator } from '../ui/StatusIndicator';
import { api } from '../../utils/apiClient';
import { UnifiedCard, UnifiedButton } from '../../design-system';

interface Wallet {
  id: number;
  wallet_name: string;
  wallet_address: string;
  network: string;
  is_active: boolean;
}

interface WalletBalance {
  wallet_id: number;
  balances: Record<string, { amount: number; usd_value: number }>;
  total_usd: number;
}

interface CryptoWalletBalancesCardProps {
  limit?: number;
}

export const CryptoWalletBalancesCard: React.FC<CryptoWalletBalancesCardProps> = ({ 
  limit = 5 
}) => {
  const { t } = useLanguage();
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [walletBalances, setWalletBalances] = useState<Record<number, WalletBalance>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWallets = useCallback(async () => {
    try {
      const response = await api.get('/trust-wallet/wallets?active_only=true');
      if (response.ok) {
        const data = await api.parseResponse(response);
        const walletsList = data.wallets || data || [];
        setWallets(walletsList.slice(0, limit));
      } else {
        setWallets([]);
      }
    } catch (err) {
      console.error('Error fetching wallets:', err);
      setWallets([]);
    }
  }, [limit]);

  const fetchWalletBalance = useCallback(async (walletId: number) => {
    try {
      const response = await api.get(`/trust-wallet/wallets/${walletId}/balance`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        const balanceData = data.success && data.data ? data.data : data;
        setWalletBalances(prev => ({
          ...prev,
          [walletId]: balanceData
        }));
      }
    } catch (err) {
      console.error(`Error fetching balance for wallet ${walletId}:`, err);
    }
  }, []);

  const loadAllBalances = useCallback(async () => {
    if (wallets.length === 0) return;
    
    setRefreshing(true);
    try {
      await Promise.all(wallets.map(wallet => fetchWalletBalance(wallet.id)));
    } finally {
      setRefreshing(false);
    }
  }, [wallets, fetchWalletBalance]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchWallets();
      setLoading(false);
    };
    loadData();
  }, [fetchWallets]);

  useEffect(() => {
    if (wallets.length > 0) {
      loadAllBalances();
    }
  }, [wallets, loadAllBalances]);

  const handleRefresh = useCallback(() => {
    loadAllBalances();
  }, [loadAllBalances]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatTokenAmount = (amount: number) => {
    if (amount >= 0.0001) {
      return amount.toLocaleString('en-US', { maximumFractionDigits: 6, minimumFractionDigits: 0 });
    }
    return amount.toExponential(2);
  };

  if (loading) {
    return (
      <UnifiedCard
        variant="default"
        header={{
          title: (
            <div className="flex items-center gap-2">
              <Wallet className="w-4 h-4 text-gray-600" />
              <span className="h-5 bg-gray-200 rounded w-40 animate-pulse"></span>
            </div>
          ),
        }}
        padding="md"
      >
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </UnifiedCard>
    );
  }

  if (error) {
    return (
      <UnifiedCard
        variant="default"
        header={{
          title: (
            <div className="flex items-center gap-2">
              <Wallet className="w-4 h-4 text-gray-600" />
              <span>Crypto Wallet Balances</span>
            </div>
          ),
        }}
        padding="md"
      >
        <p className="text-sm text-gray-500">{error}</p>
      </UnifiedCard>
    );
  }

  const totalUsdValue = Object.values(walletBalances).reduce((sum, balance) => {
    return sum + (balance?.total_usd || 0);
  }, 0);

  return (
    <UnifiedCard
      variant="default"
      header={{
        title: (
          <div className="flex items-center gap-2">
            <Wallet className="w-4 h-4 text-gray-600" />
            <span className="text-base font-semibold text-gray-900">Crypto Wallet Balances</span>
          </div>
        ),
        actions: (
          <div className="flex items-center gap-2">
            <UnifiedButton
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-1.5 h-auto min-w-0 hover:bg-gray-100"
            >
              <RefreshCw className={`w-4 h-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
            </UnifiedButton>
            <StatusIndicator status={refreshing ? "syncing" : "online"} size="sm" showLabel={false} pulse={!refreshing} />
          </div>
        ),
      }}
      padding="md"
      className="hover:shadow-md transition-shadow duration-200"
    >
      {wallets.length === 0 ? (
        <div className="text-center py-8">
          <Wallet className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-500">No active wallets</p>
        </div>
      ) : (
        <>
          {/* Total USD Value */}
          {totalUsdValue > 0 && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Total Value</span>
                <span className="text-lg font-bold text-gray-900">{formatCurrency(totalUsdValue)}</span>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {wallets.map((wallet) => {
              const balance = walletBalances[wallet.id];
              const walletTotalUsd = balance?.total_usd || 0;
              const balances = balance?.balances || {};

              return (
                <div
                  key={wallet.id}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 hover:border-gray-300 transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {wallet.wallet_name}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {wallet.network} • {wallet.wallet_address.slice(0, 8)}...{wallet.wallet_address.slice(-6)}
                      </p>
                    </div>
                    {walletTotalUsd > 0 && (
                      <div className="text-right ml-3">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatCurrency(walletTotalUsd)}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* Token Balances */}
                  {Object.keys(balances).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200 space-y-1.5">
                      {Object.entries(balances).slice(0, 3).map(([token, balanceData]: [string, any]) => (
                        <div key={token} className="flex items-center justify-between text-xs">
                          <span className="text-gray-600 font-medium">{token}</span>
                          <div className="text-right">
                            <span className="text-gray-900 font-semibold">
                              {formatTokenAmount(balanceData.amount)}
                            </span>
                            {balanceData.usd_value > 0 && (
                              <span className="text-gray-500 ml-2">
                                ({formatCurrency(balanceData.usd_value)})
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      {Object.keys(balances).length > 3 && (
                        <p className="text-xs text-gray-500 mt-1.5">
                          +{Object.keys(balances).length - 3} more tokens
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </UnifiedCard>
  );
};

export default CryptoWalletBalancesCard;

