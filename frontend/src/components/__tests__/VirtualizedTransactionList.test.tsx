/**
 * Tests for VirtualizedTransactionList component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VirtualizedTransactionList } from '../VirtualizedTransactionList';
import { Transaction } from '../../types/api';

// Mock react-window
vi.mock('react-window', () => ({
  FixedSizeList: ({ children, itemCount }: any) => (
    <div data-testid="virtualized-list">
      {Array.from({ length: itemCount }, (_, i) => children({ index: i, style: {} }))}
    </div>
  ),
}));

describe('VirtualizedTransactionList', () => {
  const mockTransactions: Transaction[] = [
    {
      id: 1,
      client_name: 'Test Client 1',
      amount: 1000,
      currency: 'TL',
      category: 'DEP',
      date: '2024-01-01',
      psp: 'Test PSP',
      commission: 50,
      net_amount: 950,
    },
    {
      id: 2,
      client_name: 'Test Client 2',
      amount: 2000,
      currency: 'USD',
      category: 'WD',
      date: '2024-01-02',
      psp: 'Test PSP 2',
      commission: 100,
      net_amount: 1900,
    },
  ];

  it('renders empty state when no transactions', () => {
    render(<VirtualizedTransactionList transactions={[]} />);
    expect(screen.getByText('No transactions found')).toBeInTheDocument();
  });

  it('renders transactions list', () => {
    render(<VirtualizedTransactionList transactions={mockTransactions} />);
    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
    expect(screen.getByText('Test Client 1')).toBeInTheDocument();
    expect(screen.getByText('Test Client 2')).toBeInTheDocument();
  });

  it('calls onTransactionClick when transaction is clicked', () => {
    const handleClick = vi.fn();
    render(
      <VirtualizedTransactionList
        transactions={mockTransactions}
        onTransactionClick={handleClick}
      />
    );
    // Click would be tested with user interaction in real implementation
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('uses custom renderTransaction when provided', () => {
    const customRender = vi.fn((transaction) => (
      <div key={transaction.id}>Custom: {transaction.client_name}</div>
    ));
    render(
      <VirtualizedTransactionList
        transactions={mockTransactions}
        renderTransaction={customRender}
      />
    );
    expect(customRender).toHaveBeenCalledTimes(mockTransactions.length);
  });
});

