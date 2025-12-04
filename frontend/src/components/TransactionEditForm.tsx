import React, { useState, useEffect } from 'react';
import { Save, X, AlertCircle, DollarSign, Shield, CheckCircle, Info } from 'lucide-react';
import { api } from '../utils/apiClient';
import { formatCurrency } from '../utils/currencyUtils';
import CurrencyConversionModal from './CurrencyConversionModal';

interface Transaction {
  id: number;
  client_name: string;
  company?: string;
  company_order?: string;
  iban?: string;
  payment_method?: string;
  category: string;
  amount: number;
  commission: number;
  net_amount: number;
  currency?: string;
  psp?: string;
  notes?: string;
  date?: string;
  created_at?: string;
  updated_at?: string;
  amount_tl?: number;
  commission_tl?: number;
  net_amount_tl?: number;
  exchange_rate?: number;
}

interface TransactionEditFormProps {
  transaction: Transaction;
  onSave: (updatedTransaction: Transaction) => void;
  onCancel: () => void;
  dropdownOptions: {
    categories: string[];
    psps: string[];
    payment_methods: string[];
    companies: string[];
    currencies: string[];
  };
}

const TransactionEditForm: React.FC<TransactionEditFormProps> = ({
  transaction,
  onSave,
  onCancel,
  dropdownOptions = { categories: [], psps: [], payment_methods: [], companies: [], currencies: [] },
}) => {
  // Debug: Log the transaction data being received
  console.log('🔄 TransactionEditForm received transaction:', transaction);
  console.log('🔄 TransactionEditForm received dropdownOptions:', dropdownOptions);
  console.log('🔄 TransactionEditForm dropdownOptions details:', {
    psps: dropdownOptions.psps?.length || 0,
    payment_methods: dropdownOptions.payment_methods?.length || 0,
    categories: dropdownOptions.categories?.length || 0,
    companies: dropdownOptions.companies?.length || 0,
    currencies: dropdownOptions.currencies?.length || 0
  });

  const [formData, setFormData] = useState({
    client_name: transaction.client_name || '',
    company: transaction.company || transaction.company_order || '',
    iban: transaction.iban || '',
    payment_method: transaction.payment_method || '',
    category: transaction.category || '',
    amount: transaction.amount?.toString() || '',
    currency: transaction.currency || 'TL',
    psp: transaction.psp || '',
    notes: transaction.notes || '',
    date: transaction.date ? transaction.date.split('T')[0] : new Date().toISOString().split('T')[0],
  });

  // Manual commission state
  const [showManualCommission, setShowManualCommission] = useState(false);
  const [securityCode, setSecurityCode] = useState('');
  const [manualCommission, setManualCommission] = useState('');
  const [securityCodeVerified, setSecurityCodeVerified] = useState(false);
  const [securityCodeError, setSecurityCodeError] = useState('');

  // Debug: Log the initialized form data
  console.log('🔄 TransactionEditForm initialized formData:', formData);
  console.log('🔄 Form data values:', {
    payment_method: formData.payment_method,
    category: formData.category,
    psp: formData.psp,
    company: formData.company
  });

  // Update form data when transaction prop changes
  useEffect(() => {
    setFormData({
      client_name: transaction.client_name || '',
      company: transaction.company || transaction.company_order || '',
      iban: transaction.iban || '',
      payment_method: transaction.payment_method || '',
      category: transaction.category || '',
      amount: transaction.amount?.toString() || '',
      currency: transaction.currency || 'TL',
      psp: transaction.psp || '',
      notes: transaction.notes || '',
      date: transaction.date ? transaction.date.split('T')[0] : new Date().toISOString().split('T')[0],
    });
    console.log('🔄 TransactionEditForm updated formData from transaction:', transaction);
  }, [transaction]);

  // Ensure current values are included in dropdown options
  const enhancedDropdownOptions = {
    ...dropdownOptions,
    payment_methods: [
      ...new Set([
        ...(dropdownOptions.payment_methods || []),
        ...(transaction.payment_method ? [transaction.payment_method] : [])
      ])
    ],
    categories: [
      ...new Set([
        ...(dropdownOptions.categories || []),
        ...(transaction.category ? [transaction.category] : [])
      ])
    ],
    psps: [
      ...new Set([
        ...(dropdownOptions.psps || []),
        ...(transaction.psp ? [transaction.psp] : [])
      ])
    ],
    companies: [
      ...new Set([
        ...(dropdownOptions.companies || []),
        ...(transaction.company ? [transaction.company] : []),
        ...(transaction.company_order ? [transaction.company_order] : [])
      ])
    ],
    currencies: [
      ...new Set([
        ...(dropdownOptions.currencies || []),
        ...(transaction.currency ? [transaction.currency] : [])
      ])
    ]
  };

  // Debug: Log the enhanced dropdown options
  console.log('🔄 TransactionEditForm enhanced dropdown options:', enhancedDropdownOptions);
  console.log('🔄 TransactionEditForm enhanced options counts:', {
    psps: enhancedDropdownOptions.psps?.length || 0,
    payment_methods: enhancedDropdownOptions.payment_methods?.length || 0,
    categories: enhancedDropdownOptions.categories?.length || 0,
    companies: enhancedDropdownOptions.companies?.length || 0,
    currencies: enhancedDropdownOptions.currencies?.length || 0
  });
  console.log('🔄 TransactionEditForm PSP options list:', enhancedDropdownOptions.psps);
  console.log('🔄 TransactionEditForm Payment method options list:', enhancedDropdownOptions.payment_methods);
  console.log('🔄 TransactionEditForm Currency options list:', enhancedDropdownOptions.currencies);


  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showExchangeRateSection, setShowExchangeRateSection] = useState(false);
  const [showCurrencyModal, setShowCurrencyModal] = useState(false);
  const [eurRate, setEurRate] = useState(transaction.exchange_rate?.toString() || '');
  const [usdRate, setUsdRate] = useState(transaction.exchange_rate?.toString() || '');
  const [convertedAmounts, setConvertedAmounts] = useState<{
    amount_try: number;
    commission_try: number;
    net_amount_try: number;
  } | null>(null);
  const [rateApplied, setRateApplied] = useState(false);

  // Check if exchange rate section should be shown
  useEffect(() => {
    if ((formData.currency === 'EUR' || formData.currency === 'USD') && formData.date) {
      setShowExchangeRateSection(true);
    } else {
      setShowExchangeRateSection(false);
    }
  }, [formData.currency, formData.date]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
    
    // Reset converted amounts when amount or currency changes
    if (field === 'amount' || field === 'currency') {
      setConvertedAmounts(null);
      setRateApplied(false);
    }
    
    // Show currency modal when USD is selected
    if (field === 'currency' && value === 'USD') {
      setShowCurrencyModal(true);
    }
  };

  const handleCurrencyRateSelect = (rate: number) => {
    setUsdRate(rate.toString());
    setShowCurrencyModal(false);
    // Reset converted amounts when rate is updated
    setConvertedAmounts(null);
    setRateApplied(false);
  };

  const handleApplyExchangeRate = () => {
    const amount = parseFloat(formData.amount) || 0;
    let rate = 0;
    
    if (formData.currency === 'USD') {
      rate = parseFloat(usdRate) || 0;
    } else if (formData.currency === 'EUR') {
      rate = parseFloat(eurRate) || 0;
    }
    
    if (rate > 0 && amount > 0) {
      const amount_try = amount * rate;
      const commission_try = 0; // Commission will be calculated by backend
      const net_amount_try = amount_try - commission_try;
      
      setConvertedAmounts({
        amount_try,
        commission_try,
        net_amount_try
      });
      setRateApplied(true);
      setError(null);
    } else {
      setError('Please enter valid amount and exchange rate.');
    }
  };

  const validateForm = () => {
    if (!formData.client_name.trim()) {
      setError('Client name is required.');
      return false;
    }
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      setError('Amount must be a positive number.');
      return false;
    }
    if (formData.currency === 'EUR' && !eurRate) {
      setError('Please enter the EUR exchange rate.');
      return false;
    }
    if (formData.currency === 'USD' && !usdRate) {
      setError('Please enter the USD exchange rate.');
      return false;
    }
    return true;
  };

  const handleSecurityCodeVerification = () => {
    if (securityCode === '4561') {
      setSecurityCodeVerified(true);
      setSecurityCodeError('');
      setShowManualCommission(true);
    } else {
      setSecurityCodeError('Invalid security code. Please try again.');
      setSecurityCodeVerified(false);
    }
  };

  const handleManualCommissionToggle = () => {
    if (!securityCodeVerified) {
      setShowManualCommission(false);
      setSecurityCode('');
      setSecurityCodeError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const updateData = {
        ...formData,
        company_order: formData.company, // Map company to company_order for backend
        amount: parseFloat(formData.amount),
        eur_rate: formData.currency === 'EUR' ? parseFloat(eurRate) : undefined,
        usd_rate: formData.currency === 'USD' ? parseFloat(usdRate) : undefined,
        // Add manual commission if enabled and provided
        ...(securityCodeVerified && manualCommission && parseFloat(manualCommission) > 0 && {
          manual_commission_rate: parseFloat(manualCommission),
          use_manual_commission: true
        })
      };

      console.log('🔄 Sending transaction update data:', updateData);

      const response = await api.put(`/transactions/${transaction.id}`, updateData);
      
      console.log('🔄 Transaction update response:', response);

      // ApiClient returns ApiResponse with data, status, and ok properties
      if (response.ok && response.data) {
        const data = response.data;
        // Backend returns { status: 'success', message: '...', transaction: {...} }
        if (data.transaction) {
          onSave(data.transaction);
        } else if (data.status === 'success') {
          // If transaction object is in different location, try to find it
          console.warn('Transaction data structure differs from expected:', data);
          // Try to use the data itself if it has transaction-like structure
          if (data.id) {
            onSave(data as Transaction);
          } else {
            setError('Transaction update succeeded but data format is unexpected.');
          }
        } else {
          setError(data.message || data.error || 'Failed to update transaction.');
        }
      } else {
        // Handle error response
        const errorData = response.data || {};
        console.error('❌ Transaction update failed:', errorData);
        setError(errorData.message || errorData.error || `Failed to update transaction. Status: ${response.status}`);
      }
    } catch (err: any) {
      console.error('💥 Error updating transaction:', err);
      // Extract error message from different error formats
      const errorMessage = err?.message || err?.data?.message || err?.data?.error || 'An error occurred while updating the transaction.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-h-[80vh] overflow-y-auto overflow-x-hidden pr-2 edit-form-scroll">
      <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Client Information */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-4">Client Information</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Client Name *
            </label>
            <input
              type="text"
              value={formData.client_name}
              onChange={(e) => handleInputChange('client_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company
            </label>
            <select
              value={formData.company}
              onChange={(e) => handleInputChange('company', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
            >
              <option value="">Select Company</option>
              {enhancedDropdownOptions?.companies?.map((company) => (
                <option key={company} value={company}>
                  {company}
                </option>
              )) || []}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              IBAN
            </label>
            <input
              type="text"
              value={formData.iban}
              onChange={(e) => handleInputChange('iban', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
              placeholder="Enter IBAN"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Payment Method
            </label>
            <select
              value={formData.payment_method}
              onChange={(e) => handleInputChange('payment_method', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
            >
              <option value="">Select Payment Method</option>
              {enhancedDropdownOptions?.payment_methods?.map((method) => (
                <option key={method} value={method}>
                  {method}
                </option>
              )) || []}
            </select>
          </div>
        </div>
      </div>

      {/* Transaction Details */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-4">Transaction Details</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category *
            </label>
            <select
              value={formData.category}
              onChange={(e) => handleInputChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
              required
            >
              <option value="">Select Category</option>
              {enhancedDropdownOptions?.categories?.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              )) || []}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              PSP
            </label>
            <select
              value={formData.psp}
              onChange={(e) => handleInputChange('psp', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
            >
              <option value="">Select PSP</option>
              {enhancedDropdownOptions?.psps?.map((psp) => (
                <option key={psp} value={psp}>
                  {psp}
                </option>
              )) || []}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount *
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.amount}
              onChange={(e) => handleInputChange('amount', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Currency
            </label>
            <select
              value={formData.currency}
              onChange={(e) => handleInputChange('currency', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
            >
              <option value="TL">TL</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Transaction Date
            </label>
            <input
              type="date"
              value={formData.date}
              onChange={(e) => handleInputChange('date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
            />
          </div>
        </div>
      </div>

      {/* Exchange Rate Section */}
      {showExchangeRateSection && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Exchange Rate</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {formData.currency === 'EUR' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  EUR Rate (1 EUR = ? TL)
                </label>
                                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    value={eurRate}
                    onChange={(e) => {
                      setEurRate(e.target.value);
                      setConvertedAmounts(null);
                      setRateApplied(false);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
                    required
                  />
              </div>
            )}
            {formData.currency === 'USD' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  USD Rate (1 USD = ? TL)
                </label>
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    value={usdRate}
                    onChange={(e) => {
                      setUsdRate(e.target.value);
                      setConvertedAmounts(null);
                      setRateApplied(false);
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500 min-w-0"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrencyModal(true)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200 flex items-center justify-center space-x-2 whitespace-nowrap"
                  >
                    <DollarSign className="h-4 w-4" />
                    <span className="text-sm font-medium">Get Rate</span>
                  </button>
                </div>
                {usdRate && (
                  <p className="text-xs text-gray-600 mt-1 break-words">
                    ${formData.amount || 0} USD = ₺{((parseFloat(formData.amount) || 0) * (parseFloat(usdRate) || 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                )}
              </div>
            )}
          </div>
          
          {/* Apply Exchange Rate Button */}
          <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <button
              type="button"
              onClick={handleApplyExchangeRate}
              disabled={
                !formData.amount || 
                (formData.currency === 'USD' && !usdRate) || 
                (formData.currency === 'EUR' && !eurRate)
              }
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 whitespace-nowrap"
            >
              <span>Apply Exchange Rate</span>
            </button>
            
            {rateApplied && (
              <span className="text-sm text-green-600 font-medium text-center sm:text-right">
                ✓ Rate applied successfully
              </span>
            )}
          </div>
          
          {/* Converted Amounts Display */}
          {convertedAmounts && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg overflow-hidden">
              <h5 className="text-sm font-medium text-green-800 mb-3">Converted Amounts (Turkish Lira)</h5>
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-2">
                  <span className="text-green-700 text-sm">Amount:</span>
                  <span className="font-medium text-green-900 text-sm break-all">
                    ₺{convertedAmounts.amount_try.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-2">
                  <span className="text-green-700 text-sm">Commission:</span>
                  <span className="font-medium text-green-900 text-sm break-all">
                    ₺{convertedAmounts.commission_try.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1 sm:gap-2">
                  <span className="text-green-700 text-sm">Net Amount:</span>
                  <span className="font-medium text-green-900 text-sm break-all">
                    ₺{convertedAmounts.net_amount_try.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-green-200">
                <div className="text-xs text-green-600 break-words">
                  Exchange Rate: 1 {formData.currency} = ₺{formData.currency === 'USD' ? usdRate : eurRate}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Commission - Minimal Design */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-900">Manual Commission</h4>
          {securityCodeVerified && (
            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
              <CheckCircle className="h-3 w-3" />
              Active
            </span>
          )}
        </div>
        
        {!securityCodeVerified ? (
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="password"
                value={securityCode}
                onChange={e => setSecurityCode(e.target.value)}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Security code"
              />
              <button
                type="button"
                onClick={handleSecurityCodeVerification}
                className="px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-1 focus:ring-blue-500"
              >
                Enable
              </button>
            </div>
            {securityCodeError && (
              <p className="text-xs text-red-600">{securityCodeError}</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="number"
                step="0.01"
                value={manualCommission}
                onChange={e => setManualCommission(e.target.value)}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Commission %"
              />
              <button
                type="button"
                onClick={() => {
                  setSecurityCodeVerified(false);
                  setShowManualCommission(false);
                  setSecurityCode('');
                  setManualCommission('');
                  setSecurityCodeError('');
                }}
                className="px-3 py-2 text-sm font-medium text-gray-600 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
              >
                Disable
              </button>
            </div>
            <p className="text-xs text-gray-500">Overrides automatic PSP commission rate</p>
          </div>
        )}
      </div>

      {/* Description */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-4">Additional Information</h4>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Notes
          </label>
          <textarea
            value={formData.notes}
            onChange={(e) => handleInputChange('notes', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-gray-500 focus:border-gray-500"
            placeholder="Enter transaction notes..."
          />
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          <X className="h-4 w-4 mr-2 inline" />
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Saving...
            </div>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2 inline" />
              Save Changes
            </>
          )}
        </button>
      </div>
      </form>

      {/* Currency Conversion Modal */}
      <CurrencyConversionModal
        isOpen={showCurrencyModal}
        onClose={() => setShowCurrencyModal(false)}
        onRateSelect={handleCurrencyRateSelect}
        currentAmount={parseFloat(formData.amount) || 0}
        transactionDate={formData.date}
      />
    </div>
  );
};

export default TransactionEditForm;
