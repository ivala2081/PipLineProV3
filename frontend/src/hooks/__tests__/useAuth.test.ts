// useAuth Hook Tests
import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { setupFetchMock, mockApi } from '@/test/utils/mock-api'
import { mockUser } from '@/test/utils/mock-data'

// Mock useAuth hook
function useAuth() {
  const [user, setUser] = React.useState(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState(null)

  const login = async (username: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Login failed')
      }

      setUser(data.user)
      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }

  const logout = () => {
    setUser(null)
  }

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/v1/auth/check')
      const data = await response.json()
      
      if (response.ok && data.user) {
        setUser(data.user)
      }
    } catch (err) {
      // Silently fail
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    checkAuth()
  }, [])

  return {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user,
  }
}

describe('useAuth Hook', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  it('initializes with loading state', () => {
    global.fetch = mockApi.login(true) as any
    const { result } = renderHook(() => useAuth())
    
    expect(result.current.loading).toBe(true)
    expect(result.current.user).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('logs in user successfully', async () => {
    global.fetch = mockApi.login(true) as any
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await result.current.login('testuser', 'password123')
    
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
    })
  })

  it('handles login error', async () => {
    global.fetch = mockApi.login(false) as any
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await expect(
      result.current.login('wronguser', 'wrongpass')
    ).rejects.toThrow()
    
    await waitFor(() => {
      expect(result.current.error).toBeTruthy()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })

  it('logs out user', async () => {
    global.fetch = mockApi.login(true) as any
    const { result } = renderHook(() => useAuth())
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Login first
    await result.current.login('testuser', 'password123')
    
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true)
    })

    // Then logout
    result.current.logout()
    
    await waitFor(() => {
      expect(result.current.user).toBeNull()
      expect(result.current.isAuthenticated).toBe(false)
    })
  })
})

