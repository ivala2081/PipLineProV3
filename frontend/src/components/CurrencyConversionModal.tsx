import React, { useState, useEffect } from 'react';
import { X, DollarSign, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import { api } from '../utils/apiClient';

interface CurrencyConversionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRateSelect: (rate: number) => void;
  currentAmount: number;
  transactionDate: string;
}

interface ExchangeRate {
  rate: number;
  timestamp: string;
  source: string;
  change_24h?: number;
  volume?: number;
}

const CurrencyConversionModal: React.FC<CurrencyConversionModalProps> = ({
  isOpen,
  onClose,
  onRateSelect,
  currentAmount,
  transactionDate,
}) => {
  const [currentRate, setCurrentRate] = useState<ExchangeRate | null>(null);
  const [customRate, setCustomRate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // Fetch current USD/TRY rate
  const fetchCurrentRate = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get('/exchange-rates/current');
      const data = await api.parseResponse(response);
      
      if (response.ok && data.success && data.rate) {
        // Extract rate details from the nested structure
        const rateData = {
          rate: data.rate.rate,
          timestamp: data.rate.created_at,
          source: data.rate.source,
          change_24h: data.rate.change_24h,
          volume: data.rate.volume
        };
        
        setCurrentRate(rateData);
        setCustomRate(data.rate.rate.toFixed(4));
        setLastUpdated(new Date(data.rate.created_at).toLocaleString());
      } else {
        console.error('API Response:', data);
        setError(`Failed to fetch current exchange rate: ${data.message || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error fetching exchange rate:', err);
      setError(`Unable to fetch current exchange rate: ${err instanceof Error ? err.message : 'Network error'}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchCurrentRate();
    }
  }, [isOpen]);

  const handleUseCurrentRate = () => {
    if (currentRate) {
      onRateSelect(currentRate.rate);
      onClose();
    }
  };

  const handleUseCustomRate = () => {
    const rate = parseFloat(customRate);
    if (rate > 0) {
      onRateSelect(rate);
      onClose();
    }
  };

  const calculateTRYAmount = (rate: number) => {
    return (currentAmount * rate).toFixed(2);
  };

  const formatRateChange = (change?: number) => {
    if (!change) return null;
    const isPositive = change > 0;
    return (
      <div className={`flex items-center text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        <TrendingUp className={`h-3 w-3 mr-1 ${isPositive ? '' : 'rotate-180'}`} />
        {isPositive ? '+' : ''}{change.toFixed(4)} (24h)
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 max-w-md w-full max-h-[90vh] flex flex-col">
        {/* Header - Fixed */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-indigo-50 flex-shrink-0">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
              <DollarSign className="h-4 w-4 text-gray-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Currency Conversion</h3>
              <p className="text-sm text-gray-600">USD to TRY Exchange Rate</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
          <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Transaction Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Transaction Details</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Amount (USD):</span>
                <span className="font-medium text-gray-900">${currentAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Date:</span>
                <span className="font-medium text-gray-900">{transactionDate}</span>
              </div>
            </div>
          </div>

          {/* Current Rate Section */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
              <span className="ml-3 text-gray-600">Fetching current rate...</span>
            </div>
          ) : currentRate ? (
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">Current Market Rate</h4>
                <div className="flex items-center text-xs text-gray-700">
                  <Clock className="h-3 w-3 mr-1" />
                  Updated: {lastUpdated}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-bold text-gray-900">1 USD = ₺{currentRate.rate.toFixed(4)}</span>
                  {formatRateChange(currentRate.change_24h)}
                </div>
                
                <div className="text-sm text-gray-700">
                  <span className="font-medium">${currentAmount.toFixed(2)} USD</span>
                  <span className="mx-2">→</span>
                  <span className="font-bold">₺{calculateTRYAmount(currentRate.rate)}</span>
                </div>
              </div>

              <button
                onClick={handleUseCurrentRate}
                className="w-full mt-4 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors duration-200 flex items-center justify-center"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Use Current Rate
              </button>
            </div>
          ) : null}

          {/* Custom Rate Section */}
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Custom Exchange Rate</h4>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Manual Rate (1 USD = ? TRY)
                </label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  value={customRate}
                  onChange={(e) => setCustomRate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
                  placeholder="Enter exchange rate..."
                />
              </div>

              {customRate && parseFloat(customRate) > 0 && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-700">
                    <span className="font-medium">${currentAmount.toFixed(2)} USD</span>
                    <span className="mx-2">→</span>
                    <span className="font-bold text-gray-900">₺{calculateTRYAmount(parseFloat(customRate))}</span>
                  </div>
                </div>
              )}

              <button
                onClick={handleUseCustomRate}
                disabled={!customRate || parseFloat(customRate) <= 0}
                className="w-full bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Apply Custom Rate
              </button>
            </div>
          </div>

          {/* Rate History Hint */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs text-yellow-800">
              💡 <strong>Tip:</strong> For historical transactions, you may want to use the exchange rate that was applicable on the transaction date rather than the current rate.
            </p>
            </div>
          </div>
        </div>

        {/* Footer - Fixed */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex-shrink-0">
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors duration-200"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CurrencyConversionModal;
