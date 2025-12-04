// Mock API handlers for testing
import { vi } from 'vitest'
import { mockApiResponses } from './mock-data'

// Mock fetch responses
export function mockFetchSuccess(data: any) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => data,
    headers: new Headers(),
  })
}

export function mockFetchError(status: number, message: string) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: async () => ({ error: message }),
    headers: new Headers(),
  })
}

// API endpoint mocks
export const mockApi = {
  login: (success = true) => {
    if (success) {
      return mockFetchSuccess(mockApiResponses.login)
    }
    return mockFetchError(401, 'Invalid credentials')
  },

  getTransactions: (success = true) => {
    if (success) {
      return mockFetchSuccess(mockApiResponses.transactions)
    }
    return mockFetchError(500, 'Failed to fetch transactions')
  },

  createTransaction: (success = true) => {
    if (success) {
      return mockFetchSuccess(mockApiResponses.transactions.transactions[0])
    }
    return mockFetchError(422, 'Invalid transaction data')
  },

  getExchangeRate: (success = true) => {
    if (success) {
      return mockFetchSuccess(mockApiResponses.exchangeRate)
    }
    return mockFetchError(404, 'Exchange rate not found')
  },

  getAnalytics: (success = true) => {
    if (success) {
      return mockFetchSuccess(mockApiResponses.analytics)
    }
    return mockFetchError(500, 'Failed to fetch analytics')
  },

  getDashboard: (success = true) => {
    if (success) {
      return mockFetchSuccess(mockApiResponses.dashboard)
    }
    return mockFetchError(500, 'Failed to fetch dashboard data')
  },
}

// Helper to setup fetch mock
export function setupFetchMock() {
  global.fetch = vi.fn()
  return global.fetch
}

// Helper to reset fetch mock
export function resetFetchMock() {
  vi.clearAllMocks()
}

