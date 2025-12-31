/**
 * Virtualized Transaction List Component
 * Efficiently renders large lists of transactions using virtual scrolling
 */
import React, { useMemo, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { Transaction } from '../types/api';

interface VirtualizedTransactionListProps {
  transactions: Transaction[];
  height?: number;
  itemHeight?: number;
  onTransactionClick?: (transaction: Transaction) => void;
  renderTransaction?: (transaction: Transaction, index: number) => React.ReactNode;
}

interface ListItemProps {
  index: number;
  style: React.CSSProperties;
  data: {
    transactions: Transaction[];
    onTransactionClick?: (transaction: Transaction) => void;
    renderTransaction?: (transaction: Transaction, index: number) => React.ReactNode;
  };
}

const ListItem: React.FC<ListItemProps> = ({ index, style, data }) => {
  const { transactions, onTransactionClick, renderTransaction } = data;
  const transaction = transactions[index];

  const handleClick = useCallback(() => {
    onTransactionClick?.(transaction);
  }, [transaction, onTransactionClick]);

  if (renderTransaction) {
    return (
      <div style={style} onClick={handleClick}>
        {renderTransaction(transaction, index)}
      </div>
    );
  }

  // Default rendering
  return (
    <div
      style={style}
      onClick={handleClick}
      className="px-4 py-2 border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex justify-between items-center">
        <div className="flex-1">
          <div className="font-medium text-gray-900">{transaction.client_name}</div>
          <div className="text-sm text-gray-500">
            {transaction.date} • {transaction.category} • {transaction.psp || 'N/A'}
          </div>
        </div>
        <div className="text-right">
          <div className="font-semibold text-gray-900">
            {transaction.currency} {transaction.amount?.toLocaleString()}
          </div>
          {transaction.commission && (
            <div className="text-xs text-gray-500">
              Commission: {transaction.currency} {transaction.commission.toLocaleString()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const VirtualizedTransactionList: React.FC<VirtualizedTransactionListProps> = ({
  transactions,
  height = 600,
  itemHeight = 80,
  onTransactionClick,
  renderTransaction,
}) => {
  const itemData = useMemo(
    () => ({
      transactions,
      onTransactionClick,
      renderTransaction,
    }),
    [transactions, onTransactionClick, renderTransaction]
  );

  if (transactions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No transactions found
      </div>
    );
  }

  return (
    <div className="w-full">
      <List
        height={height}
        itemCount={transactions.length}
        itemSize={itemHeight}
        itemData={itemData}
        width="100%"
        overscanCount={5} // Render 5 extra items outside visible area for smooth scrolling
      >
        {ListItem}
      </List>
    </div>
  );
};

export default VirtualizedTransactionList;

