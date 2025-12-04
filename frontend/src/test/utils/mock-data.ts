// Mock data for testing
import { Transaction, User, ExchangeRate } from '@/types'

export const mockUser: User = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  isActive: true,
  createdAt: new Date('2024-01-01').toISOString(),
}

export const mockViewerUser: User = {
  id: 2,
  username: 'viewer',
  email: 'viewer@example.com',
  role: 'viewer',
  isActive: true,
  createdAt: new Date('2024-01-01').toISOString(),
}

export const mockTransaction: Transaction = {
  id: 1,
  date: new Date('2024-10-21').toISOString(),
  type: 'deposit',
  amount: 1000.0,
  currency: 'TRY',
  description: 'Test transaction',
  psp: 'Test PSP',
  company: 'Test Company',
  client: 'Test Client',
  createdAt: new Date('2024-10-21').toISOString(),
}

export const mockTransactions: Transaction[] = [
  {
    id: 1,
    date: new Date('2024-10-21').toISOString(),
    type: 'deposit',
    amount: 1000.0,
    currency: 'TRY',
    description: 'Test deposit 1',
    psp: 'PSP 1',
    company: 'Company A',
    client: 'Client 1',
    createdAt: new Date('2024-10-21').toISOString(),
  },
  {
    id: 2,
    date: new Date('2024-10-20').toISOString(),
    type: 'withdrawal',
    amount: 500.0,
    currency: 'USD',
    description: 'Test withdrawal',
    psp: 'PSP 2',
    company: 'Company B',
    client: 'Client 2',
    createdAt: new Date('2024-10-20').toISOString(),
  },
  {
    id: 3,
    date: new Date('2024-10-19').toISOString(),
    type: 'deposit',
    amount: 2000.0,
    currency: 'TRY',
    description: 'Test deposit 2',
    psp: 'PSP 1',
    company: 'Company A',
    client: 'Client 3',
    createdAt: new Date('2024-10-19').toISOString(),
  },
]

export const mockExchangeRate: ExchangeRate = {
  id: 1,
  date: new Date('2024-10-21').toISOString(),
  usdToTry: 30.5,
  eurToTry: 33.2,
  source: 'auto',
  isManual: false,
}

export const mockAnalyticsStats = {
  totalRevenue: 50000.0,
  totalTransactions: 150,
  activeClients: 25,
  averageTransactionValue: 333.33,
  deposits: {
    count: 100,
    amount: 75000.0,
  },
  withdrawals: {
    count: 50,
    amount: 25000.0,
  },
}

export const mockDashboardData = {
  stats: {
    totalBalance: 100000.0,
    totalDeposits: 75000.0,
    totalWithdrawals: 25000.0,
    netCash: 50000.0,
  },
  chartData: [
    { date: '2024-10-01', amount: 1000, netCash: 1000 },
    { date: '2024-10-02', amount: 2000, netCash: 3000 },
    { date: '2024-10-03', amount: 1500, netCash: 4500 },
  ],
}

// Mock API responses
export const mockApiResponses = {
  login: {
    access_token: 'mock-jwt-token',
    user: mockUser,
  },
  transactions: {
    transactions: mockTransactions,
    total: mockTransactions.length,
    page: 1,
    perPage: 10,
  },
  exchangeRate: mockExchangeRate,
  analytics: mockAnalyticsStats,
  dashboard: mockDashboardData,
}

// Factory functions for creating mock data
export function createMockTransaction(overrides: Partial<Transaction> = {}): Transaction {
  return {
    ...mockTransaction,
    ...overrides,
    id: overrides.id || Math.floor(Math.random() * 10000),
  }
}

export function createMockUser(overrides: Partial<User> = {}): User {
  return {
    ...mockUser,
    ...overrides,
    id: overrides.id || Math.floor(Math.random() * 10000),
  }
}

export function createMockExchangeRate(overrides: Partial<ExchangeRate> = {}): ExchangeRate {
  return {
    ...mockExchangeRate,
    ...overrides,
    id: overrides.id || Math.floor(Math.random() * 10000),
  }
}

