import React, { useState, useEffect, useCallback } from 'react';
import { UnifiedCard } from '../design-system';
import { Wallet, RefreshCw, TrendingUp } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { api } from '../utils/apiClient';
import { useNavigate } from 'react-router-dom';

interface Wallet {
  id: number;
  wallet_name: string;
  network: string;
  wallet_address: string;
  is_active: boolean;
}

interface WalletBalance {
  balances?: Record<string, { amount: number; usd_value: number }>;
  total_usd?: number;
  wallet_id?: number;
}

const CryptoWalletBalancesCard: React.FC = () => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [walletBalances, setWalletBalances] = useState<Record<number, WalletBalance>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [totalBalance, setTotalBalance] = useState(0);

  const fetchWallets = useCallback(async () => {
    try {
      const response = await api.get('/trust-wallet/wallets?active_only=true');
      const data = await api.parseResponse<{ wallets: Wallet[] }>(response);
      
      if (data && data.wallets) {
        setWallets(data.wallets);
        // Fetch balances for each wallet
        data.wallets.forEach(wallet => {
          fetchWalletBalance(wallet.id);
        });
      }
    } catch (error) {
      console.error('Error fetching wallets:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchWalletBalance = useCallback(async (walletId: number) => {
    try {
      const response = await api.get(`/trust-wallet/wallets/${walletId}/balance`);
      const data = await api.parseResponse<{ success: boolean; data: WalletBalance } | WalletBalance>(response);
      
      let balanceData: WalletBalance;
      if (data && typeof data === 'object' && 'success' in data && data.success && data.data) {
        balanceData = data.data;
      } else if (data && typeof data === 'object' && ('total_usd' in data || 'balances' in data)) {
        balanceData = data as WalletBalance;
      } else {
        return;
      }
      
      setWalletBalances(prev => {
        const updated = { ...prev, [walletId]: balanceData };
        
        // Calculate total balance
        const total = Object.values(updated).reduce((sum, balance) => {
          return sum + (balance.total_usd || 0);
        }, 0);
        setTotalBalance(total);
        
        return updated;
      });
    } catch (error) {
      console.error(`Error fetching balance for wallet ${walletId}:`, error);
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await fetchWallets();
    } finally {
      setRefreshing(false);
    }
  }, [fetchWallets]);

  useEffect(() => {
    fetchWallets();
  }, [fetchWallets]);

  return (
    <UnifiedCard variant="elevated" className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Wallet className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            {t('dashboard.crypto_wallets', 'Crypto Wallets')}
          </h3>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-100 rounded-lg"></div>
            </div>
          ))}
        </div>
      ) : wallets.length === 0 ? (
        <div className="text-center py-8">
          <Wallet className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-500">
            {t('dashboard.no_wallets', 'No active wallets')}
          </p>
          <button
            onClick={() => navigate('/trust')}
            className="text-xs text-gray-600 hover:text-gray-900 mt-2 underline"
          >
            {t('dashboard.add_wallet', 'Add wallet')}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Total Balance */}
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">
                {t('dashboard.total_balance', 'Total Balance')}
              </span>
              <span className="text-lg font-bold text-gray-900">
                ${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Individual Wallets */}
          {wallets.slice(0, 3).map((wallet) => {
            const balance = walletBalances[wallet.id];
            const walletTotal = balance?.total_usd || 0;
            
            return (
              <div
                key={wallet.id}
                onClick={() => navigate('/trust')}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 hover:border-gray-200 cursor-pointer transition-all duration-200"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                    <Wallet className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {wallet.wallet_name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {wallet.network}
                    </p>
                  </div>
                </div>
                <div className="text-right ml-3">
                  <p className="text-sm font-semibold text-gray-900">
                    ${walletTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            );
          })}

          {wallets.length > 3 && (
            <button
              onClick={() => navigate('/trust')}
              className="w-full text-sm font-medium text-gray-600 hover:text-gray-900 py-2 rounded-lg hover:bg-gray-50 transition-colors duration-200"
            >
              {t('dashboard.view_all_wallets', `View all ${wallets.length} wallets`)}
            </button>
          )}
        </div>
      )}
    </UnifiedCard>
  );
};

export default CryptoWalletBalancesCard;

