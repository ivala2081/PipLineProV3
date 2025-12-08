import React, { useState, useEffect, useRef } from 'react';
import { Calendar, DollarSign, TrendingUp, Edit3, Save, X, AlertCircle, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { api } from '../utils/apiClient';
import { formatCurrency } from '../utils/currencyUtils';

interface Transaction {
  id: number;
  date?: string;
  amount: number;
  currency?: string;
  category?: string;
  exchange_rate?: number;
  amount_try?: number;
  commission_try?: number;
  net_amount_try?: number;
}

interface DailyGroup {
  date: string;
  transactions: Transaction[];
  totalTRY: number;
  netBalanceTRY: number; // Net balance from daily summary API
  hasUSDTransactions: boolean;
  hasEURTransactions: boolean;
  avgExchangeRate?: number;
  avgEURRate?: number;
  nonUSDCurrencies: string[];
}

interface DailyTransactionSummaryProps {
  transactions: Transaction[];
  onTransactionUpdate?: () => void;
}

const DailyTransactionSummary: React.FC<DailyTransactionSummaryProps> = ({
  transactions,
  onTransactionUpdate,
}) => {
  const [dailyGroups, setDailyGroups] = useState<DailyGroup[]>([]);
  const [editingDate, setEditingDate] = useState<string | null>(null);
  const [newRate, setNewRate] = useState<string>('');
  const [newEURRate, setNewEURRate] = useState<string>('');
  const [editingCurrency, setEditingCurrency] = useState<'USD' | 'EUR' | 'BULK' | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Group transactions by date and fetch daily summary data
  useEffect(() => {
    const groupedByDate = transactions
      .filter(transaction => transaction.date) // Filter out transactions without dates
      .reduce((groups: { [key: string]: Transaction[] }, transaction) => {
        const date = transaction.date!.split('T')[0]; // Get date part only
        if (!groups[date]) {
          groups[date] = [];
        }
        groups[date].push(transaction);
        return groups;
      }, {});

    const fetchDailySummaryData = async () => {
      // Prepare data for all dates first
      const dailyDataMap = new Map<string, DailyGroup>();
      
      Object.entries(groupedByDate).forEach(([date, txns]) => {
        const usdTransactions = txns.filter(t => t.currency === 'USD');
        const eurTransactions = txns.filter(t => t.currency === 'EUR');
        const tryTransactions = txns.filter(t => t.currency === 'TRY' || t.currency === 'TL');
        
        // Get all non-TRY currencies
        const nonUSDCurrencies = [...new Set(
          txns
            .filter(t => t.currency && !['TRY', 'TL', 'USD'].includes(t.currency))
            .map(t => t.currency!)
        )];
        
        // Calculate total TRY using DEP + (-WD) logic
        const nativeTRY = tryTransactions.reduce((sum, t) => {
          const isWithdrawal = t.category && t.category.toUpperCase() === 'WD';
          return sum + (isWithdrawal ? -t.amount : t.amount);
        }, 0);
        
        const convertedTRY = txns
          .filter(t => t.currency && !['TRY', 'TL'].includes(t.currency))
          .reduce((sum, t) => {
            const isWithdrawal = t.category && t.category.toUpperCase() === 'WD';
            let amountTRY = 0;
            
            if (t.amount_try && t.amount_try > 0) {
              amountTRY = t.amount_try;
            } else if (t.exchange_rate && t.exchange_rate > 0) {
              amountTRY = t.amount * t.exchange_rate;
            }
            
            return sum + (isWithdrawal ? -amountTRY : amountTRY);
          }, 0);
        
        const totalTRY = nativeTRY + convertedTRY;
        
        // Calculate average exchange rates
        const usdWithRate = usdTransactions.filter(t => t.exchange_rate && t.exchange_rate > 0);
        const avgExchangeRate = usdWithRate.length > 0 
          ? usdWithRate.reduce((sum, t) => sum + (t.exchange_rate || 0), 0) / usdWithRate.length
          : undefined;
          
        const eurWithRate = eurTransactions.filter(t => t.exchange_rate && t.exchange_rate > 0);
        const avgEURRate = eurWithRate.length > 0 
          ? eurWithRate.reduce((sum, t) => sum + (t.exchange_rate || 0), 0) / eurWithRate.length
          : undefined;

        dailyDataMap.set(date, {
          date,
          transactions: txns,
          totalTRY,
          netBalanceTRY: totalTRY, // Will be updated from batch API
          hasUSDTransactions: usdTransactions.length > 0,
          hasEURTransactions: eurTransactions.length > 0,
          avgExchangeRate,
          avgEURRate,
          nonUSDCurrencies,
        });
      });

      // Fetch all summaries in ONE batch request
      const allDates = Array.from(dailyDataMap.keys());
      if (allDates.length > 0) {
        try {
          const datesParam = allDates.join(',');
          const response = await api.get(`/api/summary/batch?dates=${encodeURIComponent(datesParam)}`);
          
          if (response.ok) {
            const batchData = await api.parseResponse(response);
            if (batchData && batchData.success && batchData.summaries) {
              // Update net balance from batch API response
              Object.entries(batchData.summaries).forEach(([date, summary]: [string, any]) => {
                const dailyGroup = dailyDataMap.get(date);
                if (dailyGroup && summary.gross_balance_tl !== undefined) {
                  dailyGroup.netBalanceTRY = summary.gross_balance_tl;
                }
              });
              }
          }
        } catch (error) {
          console.warn('Failed to fetch batch daily summaries, using frontend calculations:', error);
          // Keep fallback values already set
        }
      }

      // Convert map to array and sort by date descending
      const dailyData = Array.from(dailyDataMap.values());
      dailyData.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      setDailyGroups(dailyData);
    };

    fetchDailySummaryData();
  }, [transactions]);

  const handleEditRate = (date: string, currency: 'USD' | 'EUR' | 'BULK', currentRate?: number, eurRate?: number) => {
    setEditingDate(date);
    setEditingCurrency(currency);
    if (currency === 'USD') {
      setNewRate(currentRate?.toFixed(4) || '');
    } else if (currency === 'EUR') {
      setNewEURRate(eurRate?.toFixed(4) || '');
    } else if (currency === 'BULK') {
      setNewRate(''); // For bulk, user enters rate for non-USD currencies
      setNewEURRate('');
    }
    setError(null);
  };

  const handleSaveRate = async (date: string) => {
    let rate = 0;
    let targetCurrency = '';
    
    if (editingCurrency === 'USD') {
      if (!newRate || parseFloat(newRate) <= 0) {
        setError('Please enter a valid USD exchange rate');
        return;
      }
      rate = parseFloat(newRate);
      targetCurrency = 'USD';
    } else if (editingCurrency === 'EUR') {
      if (!newEURRate || parseFloat(newEURRate) <= 0) {
        setError('Please enter a valid EUR exchange rate');
        return;
      }
      rate = parseFloat(newEURRate);
      targetCurrency = 'EUR';
    } else if (editingCurrency === 'BULK') {
      if (!newEURRate || parseFloat(newEURRate) <= 0) {
        setError('Please enter a valid exchange rate for non-USD currencies');
        return;
      }
      rate = parseFloat(newEURRate);
      targetCurrency = 'BULK'; // This will apply to all non-USD currencies
    }

    try {
      setLoading(true);
      setError(null);
      
      // Find transactions for this date
      const dateGroup = dailyGroups.find(g => g.date === date);
      if (!dateGroup) return;

      let transactionsToUpdate: Transaction[] = [];
      
      if (targetCurrency === 'USD') {
        transactionsToUpdate = dateGroup.transactions.filter(t => t.currency === 'USD');
      } else if (targetCurrency === 'EUR') {
        transactionsToUpdate = dateGroup.transactions.filter(t => t.currency === 'EUR');
      } else if (targetCurrency === 'BULK') {
        // Apply to all non-USD, non-TRY currencies
        transactionsToUpdate = dateGroup.transactions.filter(t => 
          t.currency && !['USD', 'TRY', 'TL'].includes(t.currency)
        );
      }
      
      // Optimistically update the local state for immediate UI feedback
      setDailyGroups(prevGroups => {
        return prevGroups.map(group => {
          if (group.date === date) {
            // Update transactions with new rate
            const updatedTransactions = group.transactions.map(t => {
              if (transactionsToUpdate.some(tu => tu.id === t.id)) {
                return { ...t, exchange_rate: rate, amount_try: t.amount * rate };
              }
              return t;
            });
            
            // Recalculate group averages and totals
            const usdWithRate = updatedTransactions.filter(t => t.currency === 'USD' && t.exchange_rate && t.exchange_rate > 0);
            const avgExchangeRate = usdWithRate.length > 0 
              ? usdWithRate.reduce((sum, t) => sum + (t.exchange_rate || 0), 0) / usdWithRate.length
              : group.avgExchangeRate;
              
            const eurWithRate = updatedTransactions.filter(t => t.currency === 'EUR' && t.exchange_rate && t.exchange_rate > 0);
            const avgEURRate = eurWithRate.length > 0 
              ? eurWithRate.reduce((sum, t) => sum + (t.exchange_rate || 0), 0) / eurWithRate.length
              : group.avgEURRate;
            
            return {
              ...group,
              transactions: updatedTransactions,
              avgExchangeRate,
              avgEURRate
            };
          }
          return group;
        });
      });
      
      // Update each transaction with the new rate
      const updatePromises = transactionsToUpdate.map(transaction => 
        api.put(`/api/v1/transactions/${transaction.id}`, {
          exchange_rate: rate,
        })
      );

      await Promise.all(updatePromises);
      
      // Cancel edit mode
      setEditingDate(null);
      setEditingCurrency(null);
      setNewRate('');
      setNewEURRate('');
      
      // Notify parent component to refresh data
      if (onTransactionUpdate) {
        onTransactionUpdate();
      }
      
    } catch (err) {
      console.error('Error updating exchange rates:', err);
      setError('Failed to update exchange rates');
      // Revert optimistic update by notifying parent to refresh
      if (onTransactionUpdate) {
        onTransactionUpdate();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingDate(null);
    setEditingCurrency(null);
    setNewRate('');
    setNewEURRate('');
    setError(null);
  };

  const handleFetchRate = async (date: string) => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch rate from yfinance
      const response = await api.post(`/api/v1/exchange-rates/${date}/fetch`);
      
      if (response && (response as any).success && (response as any).data) {
        const fetchedRate = (response as any).data.rate;
        
        // Populate the appropriate input field based on editing currency
        if (editingCurrency === 'USD') {
          setNewRate(fetchedRate.toString());
        } else if (editingCurrency === 'EUR' || editingCurrency === 'BULK') {
          setNewEURRate(fetchedRate.toString());
        }
      } else {
        setError('Failed to fetch rate from yfinance');
      }
    } catch (err: any) {
      console.error('Error fetching rate from yfinance:', err);
      setError(err.response?.data?.error || 'Failed to fetch rate from yfinance');
    } finally {
      setLoading(false);
    }
  };

  const checkScrollPosition = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1);
    }
  };

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({
        left: -400,
        behavior: 'smooth'
      });
      setTimeout(checkScrollPosition, 300);
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({
        left: 400,
        behavior: 'smooth'
      });
      setTimeout(checkScrollPosition, 300);
    }
  };

  // Check scroll position when dailyGroups change
  useEffect(() => {
    checkScrollPosition();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkScrollPosition);
      return () => container.removeEventListener('scroll', checkScrollPosition);
    }
    return undefined;
  }, [dailyGroups]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (dailyGroups.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center">
        <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Transactions Found</h3>
        <p className="text-gray-600">Add some transactions to see daily summaries here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Daily Transaction Summary</h2>
          <p className="text-sm text-gray-600">Overview of transactions grouped by date with currency conversion rates</p>
        </div>
        {/* Scroll Navigation Controls */}
        {dailyGroups.length > 1 && (
          <div className="flex items-center space-x-2">
            <button
              onClick={scrollLeft}
              disabled={!canScrollLeft}
              className={`p-2 rounded-lg transition-colors duration-200 ${
                canScrollLeft 
                  ? 'bg-gray-100 hover:bg-gray-200 text-gray-600' 
                  : 'bg-gray-50 text-gray-300 cursor-not-allowed'
              }`}
              aria-label="Scroll left"
              title="Scroll left"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={scrollRight}
              disabled={!canScrollRight}
              className={`p-2 rounded-lg transition-colors duration-200 ${
                canScrollRight 
                  ? 'bg-gray-100 hover:bg-gray-200 text-gray-600' 
                  : 'bg-gray-50 text-gray-300 cursor-not-allowed'
              }`}
              aria-label="Scroll right"
              title="Scroll right"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            <div className="text-xs text-gray-500 ml-2">
              {dailyGroups.length} day{dailyGroups.length !== 1 ? 's' : ''}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-3" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Scrollable Container */}
      <div 
        ref={scrollContainerRef}
        className="overflow-x-auto pb-4 relative"
        style={{ 
          scrollbarWidth: 'thin',
          scrollbarColor: '#CBD5E0 #F7FAFC'
        }}
      >
        {/* Scroll indicator shadows */}
        {canScrollLeft && (
          <div className="absolute left-0 top-0 bottom-4 w-8 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
        )}
        {canScrollRight && (
          <div className="absolute right-0 top-0 bottom-4 w-8 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />
        )}
        <div className="flex space-x-6" style={{ minWidth: 'max-content' }}>
        {dailyGroups.map((group) => (
          <div key={group.date} className="bg-white rounded-lg border border-gray-200 shadow-sm flex-shrink-0" style={{ width: '400px' }}>
            {/* Date Header */}
            <div className="border-b border-gray-100 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Calendar className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{formatDate(group.date)}</h3>
                    <p className="text-sm text-gray-600">{group.transactions.length} transactions</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Net Balance (TRY)</p>
                    <p className="text-lg font-semibold text-gray-900">
                      ₺{group.netBalanceTRY.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Transaction Details */}
            <div className="px-6 py-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Transaction Breakdown */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-700">Transaction Breakdown</h4>
                    <span className="text-xs text-gray-500">{group.transactions.length} transactions</span>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">Native TRY</span>
                        <span className="text-md font-medium text-gray-900">
                          ₺{group.transactions
                            .filter(t => t.currency === 'TRY' || t.currency === 'TL')
                            .reduce((sum, t) => sum + t.amount, 0)
                            .toFixed(2)}
                        </span>
                      </div>
                      {group.hasUSDTransactions && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">USD → TRY</span>
                          <span className="text-md font-medium text-gray-900">
                            ₺{group.transactions
                              .filter(t => t.currency === 'USD')
                              .reduce((sum, t) => {
                                if (t.amount_try && t.amount_try > 0) {
                                  return sum + t.amount_try;
                                } else if (t.exchange_rate && t.exchange_rate > 0) {
                                  return sum + (t.amount * t.exchange_rate);
                                }
                                return sum;
                              }, 0)
                              .toFixed(2)}
                          </span>
                        </div>
                      )}
                      {group.hasEURTransactions && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">EUR → TRY</span>
                          <span className="text-md font-medium text-gray-900">
                            ₺{group.transactions
                              .filter(t => t.currency === 'EUR')
                              .reduce((sum, t) => {
                                if (t.amount_try && t.amount_try > 0) {
                                  return sum + t.amount_try;
                                } else if (t.exchange_rate && t.exchange_rate > 0) {
                                  return sum + (t.amount * t.exchange_rate);
                                }
                                return sum;
                              }, 0)
                              .toFixed(2)}
                          </span>
                        </div>
                      )}
                      {group.nonUSDCurrencies.length > 0 && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">{group.nonUSDCurrencies.join(', ')} → TRY</span>
                          <span className="text-md font-medium text-gray-900">
                            ₺{group.transactions
                              .filter(t => t.currency && group.nonUSDCurrencies.includes(t.currency))
                              .reduce((sum, t) => {
                                if (t.amount_try && t.amount_try > 0) {
                                  return sum + t.amount_try;
                                } else if (t.exchange_rate && t.exchange_rate > 0) {
                                  return sum + (t.amount * t.exchange_rate);
                                }
                                return sum;
                              }, 0)
                              .toFixed(2)}
                          </span>
                        </div>
                      )}
                      <div className="border-t border-gray-200 pt-2 mt-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-gray-800">Total (All Converted to TRY)</span>
                          <span className="text-lg font-bold text-gray-900">₺{group.totalTRY.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-sm font-semibold text-green-800">Net Balance (Daily Summary)</span>
                          <span className="text-lg font-bold text-green-900">₺{group.netBalanceTRY.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Exchange Rate Management */}
                {(group.hasUSDTransactions || group.hasEURTransactions || group.nonUSDCurrencies.length > 0) && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-700">Exchange Rates</h4>
                      <span className="text-xs text-gray-500">Foreign → TRY</span>
                    </div>
                    
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="space-y-3">
                        {/* USD Rate */}
                        {group.hasUSDTransactions && (
                          <div className="border-b border-green-200 pb-2">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-green-600">USD/TRY Rate</span>
                              {(!editingDate || editingDate !== group.date || editingCurrency !== 'USD') && (
                                <button
                                  onClick={() => handleEditRate(group.date, 'USD', group.avgExchangeRate)}
                                  className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
                                >
                                  <Edit3 className="h-3 w-3" />
                                  <span>Edit USD</span>
                                </button>
                              )}
                            </div>
                            
                            {editingDate === group.date && editingCurrency === 'USD' ? (
                              <div className="space-y-2">
                                <input
                                  type="number"
                                  step="0.0001"
                                  min="0"
                                  value={newRate}
                                  onChange={(e) => setNewRate(e.target.value)}
                                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                                  placeholder="Enter USD/TRY rate"
                                />
                                <div className="flex items-center space-x-2 flex-wrap">
                                  <button
                                    onClick={() => handleFetchRate(group.date)}
                                    disabled={loading}
                                    className="flex items-center space-x-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                  >
                                    <Download className="h-3 w-3" />
                                    <span>Get Rate</span>
                                  </button>
                                  <button
                                    onClick={() => handleSaveRate(group.date)}
                                    disabled={loading}
                                    className="flex items-center space-x-1 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
                                  >
                                    <Save className="h-3 w-3" />
                                    <span>Apply</span>
                                  </button>
                                  <button
                                    onClick={handleCancelEdit}
                                    className="flex items-center space-x-1 px-2 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700 transition-colors"
                                  >
                                    <X className="h-3 w-3" />
                                    <span>Cancel</span>
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm font-medium text-green-900">
                                {group.avgExchangeRate ? `₺${group.avgExchangeRate.toFixed(4)}` : 'Not set'}
                              </div>
                            )}
                          </div>
                        )}

                        {/* EUR Rate */}
                        {group.hasEURTransactions && (
                          <div className="border-b border-green-200 pb-2">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-green-600">EUR/TRY Rate</span>
                              {(!editingDate || editingDate !== group.date || editingCurrency !== 'EUR') && (
                                <button
                                  onClick={() => handleEditRate(group.date, 'EUR', undefined, group.avgEURRate)}
                                  className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
                                >
                                  <Edit3 className="h-3 w-3" />
                                  <span>Edit EUR</span>
                                </button>
                              )}
                            </div>
                            
                            {editingDate === group.date && editingCurrency === 'EUR' ? (
                              <div className="space-y-2">
                                <input
                                  type="number"
                                  step="0.0001"
                                  min="0"
                                  value={newEURRate}
                                  onChange={(e) => setNewEURRate(e.target.value)}
                                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                                  placeholder="Enter EUR/TRY rate"
                                />
                                <div className="flex items-center space-x-2 flex-wrap">
                                  <button
                                    onClick={() => handleFetchRate(group.date)}
                                    disabled={loading}
                                    className="flex items-center space-x-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                  >
                                    <Download className="h-3 w-3" />
                                    <span>Get Rate</span>
                                  </button>
                                  <button
                                    onClick={() => handleSaveRate(group.date)}
                                    disabled={loading}
                                    className="flex items-center space-x-1 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
                                  >
                                    <Save className="h-3 w-3" />
                                    <span>Apply</span>
                                  </button>
                                  <button
                                    onClick={handleCancelEdit}
                                    className="flex items-center space-x-1 px-2 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700 transition-colors"
                                  >
                                    <X className="h-3 w-3" />
                                    <span>Cancel</span>
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm font-medium text-green-900">
                                {group.avgEURRate ? `₺${group.avgEURRate.toFixed(4)}` : 'Not set'}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Bulk Rate for Other Currencies */}
                        {group.nonUSDCurrencies.length > 0 && (
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-green-600">
                                Other Currencies ({group.nonUSDCurrencies.join(', ')}) Rate
                              </span>
                              {(!editingDate || editingDate !== group.date || editingCurrency !== 'BULK') && (
                                <button
                                  onClick={() => handleEditRate(group.date, 'BULK')}
                                  className="flex items-center space-x-1 text-xs text-orange-600 hover:text-orange-800 transition-colors"
                                >
                                  <Edit3 className="h-3 w-3" />
                                  <span>Set Bulk Rate</span>
                                </button>
                              )}
                            </div>
                            
                            {editingDate === group.date && editingCurrency === 'BULK' ? (
                              <div className="space-y-2">
                                <input
                                  type="number"
                                  step="0.0001"
                                  min="0"
                                  value={newEURRate}
                                  onChange={(e) => setNewEURRate(e.target.value)}
                                  className="w-full px-2 py-1 text-sm border border-orange-300 rounded focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                  placeholder={`Enter rate for ${group.nonUSDCurrencies.join(', ')}/TRY`}
                                />
                                <div className="flex items-center space-x-2 flex-wrap">
                                  <button
                                    onClick={() => handleFetchRate(group.date)}
                                    disabled={loading}
                                    className="flex items-center space-x-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                  >
                                    <Download className="h-3 w-3" />
                                    <span>Get Rate</span>
                                  </button>
                                  <button
                                    onClick={() => handleSaveRate(group.date)}
                                    disabled={loading}
                                    className="flex items-center space-x-1 px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 disabled:opacity-50 transition-colors"
                                  >
                                    <Save className="h-3 w-3" />
                                    <span>Apply to All</span>
                                  </button>
                                  <button
                                    onClick={handleCancelEdit}
                                    className="flex items-center space-x-1 px-2 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700 transition-colors"
                                  >
                                    <X className="h-3 w-3" />
                                    <span>Cancel</span>
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm font-medium text-orange-700">
                                Click "Set Bulk Rate" to apply rate to all {group.nonUSDCurrencies.join(', ')} transactions
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        </div>
      </div>
    </div>
  );
};

export default DailyTransactionSummary;
