import React, { memo } from 'react';
import { BarChart3, Activity } from 'lucide-react';

interface TopPerformer {
  client_name: string;
  total_volume: number;
  transaction_count: number;
  average_transaction: number;
}

interface TopPerformersCardProps {
  title: string;
  description: string;
  data: TopPerformer[];
  icon: React.ReactNode;
  iconBgColor: string;
  formatCurrency: (amount: number, currency?: string) => string;
  showVolume?: boolean;
}

const TopPerformersCard = memo<TopPerformersCardProps>(({
  title,
  description,
  data,
  icon,
  iconBgColor,
  formatCurrency,
  showVolume = true
}) => {
  return (
    <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
      <div className='px-6 py-4 border-b border-gray-200 bg-gray-50'>
        <div className='flex items-center gap-3'>
          <div className={`w-8 h-8 ${iconBgColor} rounded-md flex items-center justify-center`}>
            {icon}
          </div>
          <div>
            <h3 className='text-lg font-semibold text-gray-900'>
              {title}
            </h3>
            <p className='text-sm text-gray-600'>
              {description}
            </p>
          </div>
        </div>
      </div>
      <div className='divide-y divide-gray-100'>
        {data.map((client, index) => (
          <div key={client.client_name} className='px-6 py-4 hover:bg-gray-50 transition-colors'>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-4'>
                <div className='w-8 h-8 bg-gray-100 rounded-md flex items-center justify-center'>
                  <span className='text-sm font-medium text-gray-700'>{index + 1}</span>
                </div>
                <div>
                  <p className='font-medium text-gray-900'>{client.client_name}</p>
                  {showVolume ? (
                    <p className='text-sm text-gray-500'>{formatCurrency(client.total_volume, '₺')} total</p>
                  ) : (
                    <p className='text-sm text-gray-500'>Avg: {formatCurrency(client.average_transaction, '₺')}</p>
                  )}
                </div>
              </div>
              <div className='text-right'>
                <p className='font-semibold text-gray-900'>
                  {showVolume ? formatCurrency(client.total_volume, '₺') : client.transaction_count}
                </p>
                <p className='text-sm text-gray-500'>
                  {showVolume ? 'Total Volume' : 'Transactions'}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});

TopPerformersCard.displayName = 'TopPerformersCard';

export default TopPerformersCard;
