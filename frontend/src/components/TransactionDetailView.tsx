import React from 'react';
import { Calendar, DollarSign, User, Building, CreditCard, FileText } from 'lucide-react';
import { formatCurrency, formatCurrencyPositive } from '../utils/currencyUtils';

interface Transaction {
  id: number;
  client_name: string;
  company?: string;
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

interface TransactionDetailViewProps {
  transaction: Transaction;
}

const TransactionDetailView: React.FC<TransactionDetailViewProps> = ({ transaction }) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return 'Invalid Date';
    }
  };

  return (
    <div className="max-h-[70vh] overflow-y-auto pr-2 space-y-6 business-scrollbar">
      {/* Transaction ID */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-gray-100 p-2 rounded-lg">
            <DollarSign className="h-6 w-6 text-gray-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Transaction #{transaction.id}
            </h3>
            <p className="text-sm text-gray-500">
              Created on {formatDate(transaction.created_at)}
            </p>
          </div>
        </div>
      </div>

      {/* Client Information */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
          <User className="h-4 w-4 mr-2" />
          Client Information
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Client Name
            </label>
            <p className="text-sm text-gray-900 font-medium">{transaction.client_name}</p>
          </div>
          {transaction.company && (
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Company
              </label>
              <p className="text-sm text-gray-900 flex items-center">
                <Building className="h-4 w-4 mr-2 text-gray-400" />
                {transaction.company}
              </p>
            </div>
          )}
          {transaction.iban && (
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                IBAN
              </label>
              <p className="text-sm text-gray-900 font-mono">{transaction.iban}</p>
            </div>
          )}
          {transaction.payment_method && (
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Payment Method
              </label>
              <p className="text-sm text-gray-900 flex items-center">
                <CreditCard className="h-4 w-4 mr-2 text-gray-400" />
                {transaction.payment_method}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Transaction Details */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
          <DollarSign className="h-4 w-4 mr-2" />
          Transaction Details
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Category
            </label>
            <p className="text-sm text-gray-900">{transaction.category}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              PSP
            </label>
            <p className="text-sm text-gray-900">{transaction.psp || 'N/A'}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Transaction Date
            </label>
            <p className="text-sm text-gray-900 flex items-center">
              <Calendar className="h-4 w-4 mr-2 text-gray-400" />
              {formatDate(transaction.date)}
            </p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Currency
            </label>
            <p className="text-sm text-gray-900 font-medium">{transaction.currency || 'TL'}</p>
          </div>
        </div>
      </div>

      {/* Financial Information */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
          <DollarSign className="h-4 w-4 mr-2" />
          Financial Information
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Amount
            </label>
            <p className="text-lg font-bold text-gray-900">
              {formatCurrencyPositive(transaction.amount, transaction.currency)}
            </p>
            {transaction.amount_tl && (
              <p className="text-xs text-gray-600">
                ({formatCurrencyPositive(transaction.amount_tl, '₺')})
              </p>
            )}
          </div>
          <div className="text-center">
            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Commission
            </label>
            <p className="text-lg font-bold text-gray-900">
              {formatCurrency(transaction.commission, transaction.currency || '₺')}
            </p>
            {transaction.commission_tl && (
              <p className="text-xs text-gray-600">
                ({formatCurrency(transaction.commission_tl, '₺')})
              </p>
            )}
          </div>
          <div className="text-center">
            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Net Amount
            </label>
            <p className="text-lg font-bold text-gray-900">
              {formatCurrencyPositive(transaction.net_amount, transaction.currency || '₺')}
            </p>
            {transaction.net_amount_tl && (
              <p className="text-xs text-gray-600">
                ({formatCurrencyPositive(transaction.net_amount_tl, '₺')})
              </p>
            )}
          </div>
        </div>
        {transaction.exchange_rate && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Exchange Rate
            </label>
            <p className="text-sm text-gray-900">
              1 {transaction.currency} = {transaction.exchange_rate.toFixed(4)} TL
            </p>
          </div>
        )}
      </div>

      {/* Notes */}
      {transaction.notes && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <FileText className="h-4 w-4 mr-2" />
            Notes
          </h4>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{transaction.notes}</p>
        </div>
      )}

      {/* Timestamps */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Timestamps</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Created
            </label>
            <p className="text-gray-900">{formatDate(transaction.created_at)}</p>
          </div>
          {transaction.updated_at && (
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                Last Updated
              </label>
              <p className="text-gray-900">{formatDate(transaction.updated_at)}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransactionDetailView;
