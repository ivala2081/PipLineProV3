/**
 * Exchange Rates Display Component
 * Shows exchange rates with source information and manual override capabilities
 */

import React, { useState } from 'react';
import { 
  exchangeRatesService, 
  ExchangeRate 
} from '../services/exchangeRatesService';
import { useExchangeRates } from '../hooks/useExchangeRates';
import { useLanguage } from '../contexts/LanguageContext';

interface ExchangeRatesDisplayProps {
  date: string;
  onRateChange?: (currencyPair: string, newRate: number) => void;
  showSource?: boolean;
  showQuality?: boolean;
  showManualOverride?: boolean;
  className?: string;
}

interface ManualOverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  currencyPair: string;
  currentRate: number;
  date: string;
  onUpdate: (newRate: number, reason: string) => Promise<boolean>;
}

const ManualOverrideModal: React.FC<ManualOverrideModalProps> = ({
  isOpen,
  onClose,
  currencyPair,
  currentRate,
  date,
  onUpdate,
}) => {
  const { t } = useLanguage();
  const [newRate, setNewRate] = useState(currentRate.toString());
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const rateValue = parseFloat(newRate);
    if (isNaN(rateValue) || rateValue <= 0) {
      setError('Please enter a valid positive number');
      setLoading(false);
      return;
    }

    const validation = exchangeRatesService.validateRate(rateValue, currencyPair);
    if (!validation.isValid) {
      setError(validation.warning || 'Invalid rate');
      setLoading(false);
      return;
    }

    const success = await onUpdate(rateValue, reason || 'Manual override by user');
    if (success) {
      onClose();
    } else {
      setError('Failed to update rate');
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <h3 className="text-lg font-semibold mb-4">
          {t('exchange_rates_display.manual_override')} - {exchangeRatesService.formatCurrencyPair(currencyPair)}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('exchange_rates_display.current_rate')}
            </label>
            <div className="text-gray-600 bg-gray-50 px-3 py-2 rounded border">
              {exchangeRatesService.formatRate(currentRate, currencyPair)}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('exchange_rates_display.new_rate')} *
            </label>
            <input
              type="number"
              step="0.0001"
              value={newRate}
              onChange={(e) => setNewRate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              placeholder={t('exchange_rates_display.enter_new_rate')}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('exchange_rates_display.reason_optional')}
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              placeholder={t('exchange_rates_display.why_override')}
              rows={3}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={loading}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? t('exchange_rates_display.updating') : t('exchange_rates_display.update_rate')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ExchangeRateCard: React.FC<{
  rate: ExchangeRate;
  onManualOverride?: (currencyPair: string, currentRate: number) => void;
  showSource?: boolean;
  showQuality?: boolean;
  showManualOverride?: boolean;
}> = ({ 
  rate, 
  onManualOverride, 
  showSource = true, 
  showQuality = true, 
  showManualOverride = true 
}) => {
  const { t } = useLanguage();
  const validation = exchangeRatesService.validateRate(rate.rate, rate.currency_pair);
  const hasWarning = validation.warning && !rate.is_manual_override;

  return (
    <div className={`bg-white rounded-lg border p-4 ${
      rate.is_manual_override ? 'border-gray-300 bg-gray-50' : 'border-gray-200'
    } ${hasWarning ? 'border-yellow-300 bg-yellow-50' : ''}`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-semibold text-gray-900">
            {exchangeRatesService.formatCurrencyPair(rate.currency_pair)}
          </h4>
          <div className="text-lg font-bold text-gray-900">
            {exchangeRatesService.formatRate(rate.rate, rate.currency_pair)}
          </div>
        </div>
        
        {showManualOverride && onManualOverride && (
          <button
            onClick={() => onManualOverride(rate.currency_pair, rate.rate)}
            className="text-gray-600 hover:text-gray-800 text-sm font-medium"
            title={t('exchange_rates_display.manual_override')}
          >
            ✏️ {t('exchange_rates_display.edit')}
          </button>
        )}
      </div>

      <div className="space-y-1 text-sm text-gray-600">
        {showSource && (
          <div className="flex items-center">
            <span className="mr-2">{exchangeRatesService.getSourceIcon(rate.source)}</span>
            <span>{exchangeRatesService.getSourceDisplayName(rate.source)}</span>
            {rate.is_manual_override && (
              <span className="ml-2 text-gray-600 text-xs font-medium">
                {t('exchange_rates_display.manual_override_label')}
              </span>
            )}
          </div>
        )}

        {showQuality && (
          <div className="flex items-center">
            <span className={`mr-2 ${exchangeRatesService.getQualityColor(rate.data_quality)}`}>
              ●
            </span>
            <span className={exchangeRatesService.getQualityColor(rate.data_quality)}>
              {exchangeRatesService.getQualityDisplayName(rate.data_quality)}
            </span>
          </div>
        )}

        {rate.override_reason && (
          <div className="text-xs text-gray-500 italic">
            {t('exchange_rates_display.reason')} {rate.override_reason}
          </div>
        )}

        {hasWarning && (
          <div className="text-xs text-yellow-700 bg-yellow-100 p-2 rounded">
            ⚠️ {validation.warning}
          </div>
        )}

        <div className="text-xs text-gray-400">
          Updated: {new Date(rate.updated_at).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

export const ExchangeRatesDisplay: React.FC<ExchangeRatesDisplayProps> = ({
  date,
  onRateChange,
  showSource = true,
  showQuality = true,
  showManualOverride = true,
  className = '',
}) => {
  const { t } = useLanguage();
  const {
    rates,
    loading,
    error,
    lastUpdated,
    updateManualRate,
    refreshRates,
  } = useExchangeRates(date);

  const [manualOverrideModal, setManualOverrideModal] = useState<{
    isOpen: boolean;
    currencyPair: string;
    currentRate: number;
  }>({
    isOpen: false,
    currencyPair: '',
    currentRate: 0,
  });

  const handleManualOverride = (currencyPair: string, currentRate: number) => {
    setManualOverrideModal({
      isOpen: true,
      currencyPair,
      currentRate,
    });
  };

  const handleUpdateRate = async (newRate: number, reason: string) => {
    const success = await updateManualRate({
      date,
      currency_pair: manualOverrideModal.currencyPair,
      rate: newRate,
      reason,
    });

    if (success && onRateChange) {
      onRateChange(manualOverrideModal.currencyPair, newRate);
    }

    return success;
  };

  const handleRefreshRates = async () => {
    await refreshRates({ date });
  };

  const supportedPairs = exchangeRatesService.getSupportedPairs();

  if (loading && Object.keys(rates).length === 0) {
    return (
      <div className={`bg-white rounded-lg border p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
          <span className="ml-3 text-gray-600">{t('exchange_rates_display.loading_exchange_rates')}</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-red-200 p-6 ${className}`}>
        <div className="text-red-600 mb-4">
          <h3 className="font-semibold">{t('exchange_rates_display.error_loading_rates')}</h3>
          <p className="text-sm">{error}</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          {t('exchange_rates_display.retry')}
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border p-6 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{t('exchange_rates_display.exchange_rates')}</h3>
          <p className="text-sm text-gray-600">
            {date} • {lastUpdated ? `${t('exchange_rates_display.last_updated')} ${lastUpdated.toLocaleTimeString()}` : t('exchange_rates_display.not_loaded')}
          </p>
        </div>
        
        <button
          onClick={handleRefreshRates}
          disabled={loading}
          className="px-3 py-1 text-sm bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
        >
          {loading ? t('exchange_rates_display.refreshing') : t('exchange_rates_display.refresh')}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {supportedPairs.map((currencyPair) => {
          const rate = rates[currencyPair];
          
          if (!rate) {
            return (
              <div key={currencyPair} className="bg-gray-50 rounded-lg border border-dashed border-gray-300 p-4">
                <div className="text-gray-500 text-center">
                  <div className="font-medium">{exchangeRatesService.formatCurrencyPair(currencyPair)}</div>
                  <div className="text-sm">{t('exchange_rates_display.rate_not_available')}</div>
                </div>
              </div>
            );
          }

          return (
            <ExchangeRateCard
              key={currencyPair}
              rate={rate}
              onManualOverride={showManualOverride ? handleManualOverride : undefined}
              showSource={showSource}
              showQuality={showQuality}
              showManualOverride={showManualOverride}
            />
          );
        })}
      </div>

      <ManualOverrideModal
        isOpen={manualOverrideModal.isOpen}
        onClose={() => setManualOverrideModal({ isOpen: false, currencyPair: '', currentRate: 0 })}
        currencyPair={manualOverrideModal.currencyPair}
        currentRate={manualOverrideModal.currentRate}
        date={date}
        onUpdate={handleUpdateRate}
      />
    </div>
  );
};

export default ExchangeRatesDisplay;
