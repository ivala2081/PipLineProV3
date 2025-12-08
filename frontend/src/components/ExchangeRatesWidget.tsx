import React, { memo } from 'react';
import { Globe, RefreshCw, AlertTriangle } from 'lucide-react';

interface ExchangeRate {
  currency_pair: string;
  rate: number;
  source: string;
  data_quality: string;
  updated_at: string;
}

interface ExchangeRatesWidgetProps {
  rates: Record<string, ExchangeRate>;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onViewAll: () => void;
  formatCurrency?: (amount: number, currency: string) => string;
}

const ExchangeRatesWidget = memo<ExchangeRatesWidgetProps>(({
  rates,
  loading,
  error,
  onRefresh,
  onViewAll,
  formatCurrency
}) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-blue-100 text-blue-700';
    }
  };

  const getQualityLabel = (quality: string) => {
    switch (quality) {
      case 'closing_price':
        return 'Live';
      case 'closest_available':
        return 'Historical';
      default:
        return 'Manual';
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'closing_price':
        return 'bg-green-100 text-green-700';
      case 'closest_available':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-blue-100 text-blue-700';
    }
  };

  return (
    <div className='bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden'>
      <div className='px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-green-50 to-green-100/50'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-3'>
            <div className='w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center shadow-sm'>
              <Globe className='h-4 w-4 text-white' />
            </div>
            <div>
              <h3 className='text-lg font-bold text-gray-900'>
                Exchange Rates
              </h3>
              <p className='text-sm text-gray-600'>
                Live currency rates • Auto updates
              </p>
            </div>
          </div>
          <div className='flex items-center gap-2'>
            <button
              onClick={onRefresh}
              disabled={loading}
              className='p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50'
              title='Refresh rates'
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onViewAll}
              className='px-3 py-1.5 text-sm font-medium text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors'
            >
              View All
            </button>
          </div>
        </div>
      </div>
      <div className='p-6'>
        {loading ? (
          <div className='flex items-center justify-center py-8'>
            <div className='animate-spin rounded-full h-6 w-6 border-b-2 border-green-600'></div>
            <span className='ml-2 text-sm text-gray-600'>Loading rates...</span>
          </div>
        ) : error ? (
          <div className='flex items-center justify-center py-8 text-red-600'>
            <AlertTriangle className='h-5 w-5 mr-2' />
            <span className='text-sm'>Failed to load rates</span>
          </div>
        ) : rates && Object.keys(rates).length > 0 ? (
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
            {Object.values(rates).slice(0, 6).map((rate) => (
              <div key={rate.currency_pair} className='p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors'>
                <div className='flex items-center justify-between mb-2'>
                  <span className='text-sm font-medium text-gray-700'>{rate.currency_pair}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${getQualityColor(rate.data_quality)}`}>
                    {getQualityLabel(rate.data_quality)}
                  </span>
                </div>
                <div className='text-lg font-bold text-gray-900'>
                  {new Intl.NumberFormat('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 4
                  }).format(rate.rate)}
                </div>
                <div className='flex items-center justify-between mt-1'>
                  <span className='text-xs text-gray-500'>
                    {rate.source === 'yfinance' ? 'Yahoo Finance' : 
                     rate.source === 'manual' ? 'Manual' : rate.source}
                  </span>
                  <span className='text-xs text-gray-500'>
                    {new Date(rate.updated_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className='flex items-center justify-center py-8 text-gray-500'>
            <Globe className='h-5 w-5 mr-2' />
            <span className='text-sm'>No rates available</span>
          </div>
        )}
      </div>
    </div>
  );
});

ExchangeRatesWidget.displayName = 'ExchangeRatesWidget';

export default ExchangeRatesWidget;
