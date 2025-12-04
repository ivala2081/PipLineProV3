import React, { useState, useEffect } from 'react';
import { DollarSign, Calendar, RefreshCw, CheckCircle, AlertCircle, X, Save } from 'lucide-react';
import { api } from '../utils/apiClient';

interface USDDate {
  date: string;
  transaction_count: number;
  total_usd_amount: number;
  current_rate: number | null;
}

interface BulkUSDRatesProps {
  onRatesApplied?: () => void;
}

const BulkUSDRates: React.FC<BulkUSDRatesProps> = ({ onRatesApplied }) => {
  const [usdDates, setUsdDates] = useState<USDDate[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [rates, setRates] = useState<Record<string, string>>({});
  const [showModal, setShowModal] = useState(false);

  // Fetch USD transaction dates
  const fetchUSDDates = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get('/api/v1/bulk-rates/usd-dates');
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setUsdDates(data.usd_dates);
          
          // Initialize rates with current rates
          const initialRates: Record<string, string> = {};
          data.usd_dates.forEach((date: USDDate) => {
            if (date.current_rate) {
              initialRates[date.date] = date.current_rate.toFixed(4);
            } else {
              initialRates[date.date] = '';
            }
          });
          setRates(initialRates);
        } else {
          setError(data.error || 'Failed to fetch USD dates');
        }
      } else {
        setError('Failed to fetch USD dates');
      }
    } catch (err) {
      console.error('Error fetching USD dates:', err);
      setError('Failed to fetch USD dates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUSDDates();
  }, []);

  const handleRateChange = (date: string, value: string) => {
    setRates(prev => ({
      ...prev,
      [date]: value
    }));
  };

  const validateRates = () => {
    const errors: string[] = [];
    
    Object.entries(rates).forEach(([date, rate]) => {
      if (!rate.trim()) {
        errors.push(`Rate is required for ${date}`);
        return;
      }
      
      const rateNum = parseFloat(rate);
      if (isNaN(rateNum) || rateNum <= 0) {
        errors.push(`Invalid rate for ${date}: ${rate}`);
      }
    });
    
    return errors;
  };

  const applyRates = async () => {
    const errors = validateRates();
    if (errors.length > 0) {
      setError(errors.join(', '));
      return;
    }

    try {
      setApplying(true);
      setError(null);
      setSuccess(null);

      // Prepare rates data
      const ratesData = Object.entries(rates).map(([date, rate]) => ({
        date,
        rate: parseFloat(rate)
      }));

      const response = await api.post('/api/v1/bulk-rates/apply-multiple-usd-rates', {
        rates: ratesData
      });

      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setSuccess(`Successfully applied rates to ${data.total_updated} USD transactions`);
          setShowModal(false);
          
          // Refresh data
          await fetchUSDDates();
          
          // Notify parent component
          if (onRatesApplied) {
            onRatesApplied();
          }
        } else {
          setError(data.error || 'Failed to apply rates');
        }
      } else {
        setError('Failed to apply rates');
      }
    } catch (err) {
      console.error('Error applying rates:', err);
      setError('Failed to apply rates');
    } finally {
      setApplying(false);
    }
  };

  const applySingleRate = async (date: string, rate: string) => {
    if (!rate.trim()) {
      setError(`Rate is required for ${date}`);
      return;
    }

    const rateNum = parseFloat(rate);
    if (isNaN(rateNum) || rateNum <= 0) {
      setError(`Invalid rate for ${date}: ${rate}`);
      return;
    }

    try {
      setApplying(true);
      setError(null);
      setSuccess(null);

      const response = await api.post('/api/v1/bulk-rates/apply-usd-rate', {
        date,
        rate: rateNum
      });

      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setSuccess(data.message);
          
          // Refresh data
          await fetchUSDDates();
          
          // Notify parent component
          if (onRatesApplied) {
            onRatesApplied();
          }
        } else {
          setError(data.error || 'Failed to apply rate');
        }
      } else {
        setError('Failed to apply rate');
      }
    } catch (err) {
      console.error('Error applying rate:', err);
      setError('Failed to apply rate');
    } finally {
      setApplying(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-gray-600" />
        <span className="ml-2 text-gray-600">Loading USD transaction dates...</span>
      </div>
    );
  }

  if (usdDates.length === 0) {
    return (
      <div className="text-center p-8">
        <DollarSign className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No USD Transactions Found</h3>
        <p className="text-gray-600">There are no USD currency transactions to apply rates to.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Bulk USD Rate Management</h2>
          <p className="text-sm text-gray-600">
            Apply exchange rates to USD transactions by date to recalculate all metrics
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchUSDDates}
            disabled={loading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            <Save className="h-4 w-4 mr-2" />
            Apply All Rates
          </button>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-3" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-400 mr-3" />
            <p className="text-sm text-green-700">{success}</p>
          </div>
        </div>
      )}

      {/* USD Dates List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            USD Transaction Dates ({usdDates.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {usdDates.map((usdDate) => (
            <div key={usdDate.date} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Calendar className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">
                      {formatDate(usdDate.date)}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {usdDate.transaction_count} transactions • {formatCurrency(usdDate.total_usd_amount)}
                    </p>
                    {usdDate.current_rate && (
                      <p className="text-xs text-gray-500">
                        Current rate: {usdDate.current_rate.toFixed(4)} TRY/USD
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm font-medium text-gray-700">Rate:</label>
                    <input
                      type="number"
                      step="0.0001"
                      min="0"
                      value={rates[usdDate.date] || ''}
                      onChange={(e) => handleRateChange(usdDate.date, e.target.value)}
                      className="w-24 px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                      placeholder="0.0000"
                    />
                    <span className="text-sm text-gray-500">TRY/USD</span>
                  </div>
                  <button
                    onClick={() => applySingleRate(usdDate.date, rates[usdDate.date] || '')}
                    disabled={applying || !rates[usdDate.date]?.trim()}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {applying ? (
                      <RefreshCw className="h-3 w-3 animate-spin" />
                    ) : (
                      <CheckCircle className="h-3 w-3" />
                    )}
                    <span className="ml-1">Apply</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bulk Apply Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Apply All USD Rates
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-3">
                  This will apply the entered rates to all USD transactions on their respective dates and recalculate all metrics.
                </p>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-yellow-400 mr-2" />
                    <p className="text-sm text-yellow-700">
                      This action will update {usdDates.length} dates and recalculate all related metrics. This cannot be undone.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={applyRates}
                  disabled={applying}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
                >
                  {applying ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  {applying ? 'Applying...' : 'Apply All Rates'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkUSDRates;
