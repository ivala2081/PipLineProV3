import React from 'react';
import { Eye, Edit, Trash2, User } from 'lucide-react';
import { Button } from './ui/button';
import { formatCurrencyPositive } from '../utils/currencyUtils';

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

interface TransactionRowProps {
  transaction: Transaction;
  onView: (transaction: Transaction) => void;
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
  normalizePaymentMethodName?: (method: string) => string;
}

export default function TransactionRow({
  transaction,
  onView,
  onEdit,
  onDelete,
  normalizePaymentMethodName = (method: string) => method,
}: TransactionRowProps) {
  return (
    <tr 
      key={transaction.id} 
      className={`hover:scale-[1.02] transition-all duration-300 ease-in-out cursor-pointer ${
        transaction.category === 'WD' 
          ? 'bg-gray-100 hover:bg-gray-200' 
          : 'bg-white hover:bg-gray-50'
      }`}
    >
      <td className='px-6 py-4 whitespace-nowrap border-b border-gray-100'>
        <div className='flex items-center'>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
            transaction.category === 'WD' ? 'bg-gray-300' : 'bg-gray-100'
          }`}>
            <User className={`h-4 w-4 ${transaction.category === 'WD' ? 'text-gray-700' : 'text-gray-600'}`} />
          </div>
          <div className='text-sm font-medium text-gray-900'>
            {transaction.client_name || 'Unknown'}
          </div>
        </div>
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-100'>
        {transaction.company || 'N/A'}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-100'>
        {normalizePaymentMethodName(transaction.payment_method || 'N/A')}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-100'>
        {transaction.category || 'N/A'}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right border-b border-gray-100'>
        {formatCurrencyPositive(transaction.amount || 0, transaction.currency)}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600 text-right border-b border-gray-100'>
        {formatCurrencyPositive(transaction.commission || 0, transaction.currency)}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-600 text-right border-b border-gray-100'>
        {formatCurrencyPositive(transaction.net_amount || 0, transaction.currency)}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-100'>
        {transaction.currency || 'N/A'}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-100'>
        {transaction.psp || 'N/A'}
      </td>
      <td className='px-6 py-4 whitespace-nowrap text-center border-b border-gray-100'>
        <div className='flex items-center justify-center gap-1'>
          <Button
            onClick={() => onView(transaction)}
            variant="ghost"
            size="icon-sm"
            className='text-gray-600 hover:text-gray-900'
            title='View Details'
          >
            <Eye className='h-3 w-3' />
          </Button>
          <Button
            onClick={() => onEdit(transaction)}
            variant="ghost"
            size="icon-sm"
            className='text-green-600 hover:text-green-900'
            title='Edit Transaction'
          >
            <Edit className='h-3 w-3' />
          </Button>
          <Button
            onClick={() => onDelete(transaction)}
            variant="ghost"
            size="icon-sm"
            className='text-red-600 hover:text-red-900'
            title='Delete Transaction'
          >
            <Trash2 className='h-3 w-3' />
          </Button>
        </div>
      </td>
    </tr>
  );
}

