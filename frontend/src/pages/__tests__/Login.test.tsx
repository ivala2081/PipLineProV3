// Login Page Tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderWithProviders, screen, userEvent } from '@/test/utils/test-utils'
import { mockApi, setupFetchMock, resetFetchMock } from '@/test/utils/mock-api'

// Mock Login component - adjust based on actual component
function MockLogin() {
  const [username, setUsername] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [error, setError] = React.useState('')
  const [loading, setLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Login failed')
        return
      }

      // Success - would normally redirect or update state
      console.log('Login successful', data)
    } catch (err) {
      setError('Network error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          aria-label="Username"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-label="Password"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
        {error && <div role="alert">{error}</div>}
      </form>
    </div>
  )
}

describe('Login Page', () => {
  beforeEach(() => {
    setupFetchMock()
    resetFetchMock()
  })

  it('renders login form', () => {
    renderWithProviders(<MockLogin />)
    
    expect(screen.getByText('Login')).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('allows user to enter credentials', async () => {
    const user = userEvent.setup()
    renderWithProviders(<MockLogin />)
    
    const usernameInput = screen.getByLabelText('Username')
    const passwordInput = screen.getByLabelText('Password')
    
    await user.type(usernameInput, 'testuser')
    await user.type(passwordInput, 'password123')
    
    expect(usernameInput).toHaveValue('testuser')
    expect(passwordInput).toHaveValue('password123')
  })

  it('submits form with credentials', async () => {
    const user = userEvent.setup()
    global.fetch = mockApi.login(true) as any
    
    renderWithProviders(<MockLogin />)
    
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: /login/i }))
    
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ username: 'testuser', password: 'password123' }),
      })
    )
  })

  it('shows error message on failed login', async () => {
    const user = userEvent.setup()
    global.fetch = mockApi.login(false) as any
    
    renderWithProviders(<MockLogin />)
    
    await user.type(screen.getByLabelText('Username'), 'wronguser')
    await user.type(screen.getByLabelText('Password'), 'wrongpass')
    await user.click(screen.getByRole('button', { name: /login/i }))
    
    // Wait for error to appear
    const errorMessage = await screen.findByRole('alert')
    expect(errorMessage).toBeInTheDocument()
    expect(errorMessage).toHaveTextContent(/invalid credentials/i)
  })

  it('disables button while loading', async () => {
    const user = userEvent.setup()
    global.fetch = vi.fn().mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ access_token: 'token', user: {} })
      }), 1000))
    )
    
    renderWithProviders(<MockLogin />)
    
    await user.type(screen.getByLabelText('Username'), 'testuser')
    await user.type(screen.getByLabelText('Password'), 'password123')
    
    const submitButton = screen.getByRole('button', { name: /login/i })
    await user.click(submitButton)
    
    // Button should be disabled while loading
    expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled()
  })
})

