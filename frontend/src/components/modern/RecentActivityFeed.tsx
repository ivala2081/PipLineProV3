import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Activity, TrendingUp, TrendingDown, Clock, ArrowRight, RefreshCw } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { StatusIndicator } from '../ui/StatusIndicator';
import { api } from '../../utils/apiClient';

interface RecentTransaction {
  id: number;
  client_name: string;
  amount: number;
  currency: string;
  category: string;
  date: string;
  created_at: string;
  psp?: string;
}

interface RecentActivityFeedProps {
  limit?: number;
  onClickTransaction?: (transactionId: number) => void;
}

export const RecentActivityFeed: React.FC<RecentActivityFeedProps> = ({ 
  limit = 5,
  onClickTransaction 
}) => {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<RecentTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // useCallback ile fetch fonksiyonunu optimize et
  const fetchRecentTransactions = useCallback(async (forceRefresh = false) => {
    try {
      if (!forceRefresh) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError(null);
      
      // Cache temizle eğer force refresh ise
      if (forceRefresh) {
        api.clearCacheForUrl('transactions');
      }
      
      // API client kullanarak transaction'ları çek
      // V1 transactions endpoint'ini kullan (standardized)
      try {
        const response = await api.get(`/transactions/?per_page=${limit}&sort_by=created_at&sort_order=desc`);
        
        if (response.ok) {
          const data = await api.parseResponse(response);
          
          // Handle different response formats with type safety
          let transactionsArray: RecentTransaction[] = [];
          
          if (data && typeof data === 'object') {
            const typedData = data as any;
            if (Array.isArray(typedData.transactions)) {
              transactionsArray = typedData.transactions;
            } else if (Array.isArray(typedData.data)) {
              transactionsArray = typedData.data;
            } else if (Array.isArray(typedData)) {
              transactionsArray = typedData;
            }
          } else if (Array.isArray(data)) {
            transactionsArray = data;
          }
          
          // Limit'e göre slice yap
          setTransactions(transactionsArray.slice(0, limit));
        } else {
          // Response ok değilse boş array set et
          setTransactions([]);
          setError(null); // Empty state göster, error gösterme
        }
      } catch (fetchError) {
        // Hata durumunda boş array set et
        setTransactions([]);
        setError(null); // Empty state göster, error gösterme
      }
    } catch (err) {
      // Genel hata durumu
      setTransactions([]);
      setError(null); // Empty state göster, error gösterme
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [limit]);

  // İlk yükleme
  useEffect(() => {
    fetchRecentTransactions();
  }, [fetchRecentTransactions]);

  // Transaction update event'lerini dinle - auto-refresh
  useEffect(() => {
    const handleTransactionsUpdate = (event: any) => {
      // Yeni transaction eklendiğinde otomatik refresh yap
      if (event.detail?.action === 'created' || event.detail?.action === 'updated') {
        fetchRecentTransactions(true);
      }
    };

    window.addEventListener('transactionsUpdated', handleTransactionsUpdate);
    
    return () => {
      window.removeEventListener('transactionsUpdated', handleTransactionsUpdate);
    };
  }, [fetchRecentTransactions]);

  // useMemo ile formatCurrency fonksiyonunu optimize et
  const formatCurrency = useCallback((amount: number, currency: string = 'TRY') => {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'TRY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }, []);

  // useMemo ile formatTimeAgo fonksiyonunu optimize et
  const formatTimeAgo = useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return `${diffInSeconds}s ago`;
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes}m ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours}h ago`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days}d ago`;
    }
  }, []);

  // useCallback ile handleTransactionClick'i optimize et
  const handleTransactionClick = useCallback((transactionId: number) => {
    if (onClickTransaction) {
      onClickTransaction(transactionId);
    } else {
      navigate(`/transactions?highlight=${transactionId}`);
    }
  }, [onClickTransaction, navigate]);

  // useCallback ile handleViewAll'i optimize et
  // Clients sayfasına, transactions tab'ına yönlendir
  const handleViewAll = useCallback(() => {
    navigate('/clients?tab=transactions');
  }, [navigate]);

  // useCallback ile handleRefresh'i ekle
  const handleRefresh = useCallback(() => {
    fetchRecentTransactions(true);
  }, [fetchRecentTransactions]);

  // useMemo ile formatlanmış transaction'ları cache'le
  const formattedTransactions = useMemo(() => {
    return transactions.map(transaction => ({
      ...transaction,
      formattedAmount: formatCurrency(Math.abs(transaction.amount), transaction.currency),
      formattedTime: formatTimeAgo(transaction.created_at || transaction.date),
      isDeposit: transaction.category === 'DEP' || transaction.category === 'DEPOSIT'
    }));
  }, [transactions, formatCurrency, formatTimeAgo]);

  if (loading) {
    return (
      <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-200">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-600" />
              {t('dashboard.recent_activity') || 'Recent Activity'}
            </CardTitle>
            <StatusIndicator status="syncing" size="sm" showLabel={false} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(limit)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-gray-100 rounded-lg"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-gray-600" />
            {t('dashboard.recent_activity') || 'Recent Activity'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">{error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 group">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-gray-600 group-hover:text-gray-900 transition-colors" />
            {t('dashboard.recent_activity') || 'Recent Activity'}
          </CardTitle>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <StatusIndicator status={refreshing ? "syncing" : "online"} size="sm" showLabel={false} pulse={!refreshing} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {transactions.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No recent activity</p>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {formattedTransactions.map((transaction) => {
                const TransactionIcon = transaction.isDeposit ? TrendingUp : TrendingDown;
                
                return (
                  <div
                    key={transaction.id}
                    onClick={() => handleTransactionClick(transaction.id)}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 hover:border-gray-200 cursor-pointer transition-all duration-200 group/item"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${
                        transaction.isDeposit 
                          ? 'bg-green-100 group-hover/item:bg-green-200' 
                          : 'bg-red-100 group-hover/item:bg-red-200'
                      }`}>
                        <TransactionIcon className={`w-4 h-4 ${
                          transaction.isDeposit ? 'text-green-700' : 'text-red-700'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate group-hover/item:text-gray-950">
                          {transaction.client_name || 'Unknown Client'}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <p className="text-xs text-gray-500 truncate">
                            {transaction.psp && `${transaction.psp} • `}
                            {transaction.formattedTime}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 ml-3">
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${
                          transaction.isDeposit ? 'text-green-700' : 'text-red-700'
                        }`}>
                          {transaction.isDeposit ? '+' : '-'}{transaction.formattedAmount}
                        </p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-gray-400 group-hover/item:text-gray-600 transition-colors opacity-0 group-hover/item:opacity-100" />
                    </div>
                  </div>
                );
              })}
            </div>
            <button
              onClick={handleViewAll}
              className="mt-4 w-full text-sm font-medium text-gray-600 hover:text-gray-900 py-2 rounded-lg hover:bg-gray-50 transition-colors duration-200 flex items-center justify-center gap-1"
            >
              View all transactions
              <ArrowRight className="w-3 h-3" />
            </button>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentActivityFeed;

