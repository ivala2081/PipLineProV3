import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/apiClient';
import { logger } from '../utils/logger';

interface User {
  id: number;
  username: string;
  role: string;
  admin_level: number;
  admin_title: string;
  is_active: boolean;
  email?: string;
  created_at?: string;
  last_login?: string;
  failed_login_attempts: number;
  account_locked_until?: string;
  created_by?: number;
  permissions: Record<string, boolean>;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (
    username: string,
    password: string,
    rememberMe?: boolean
  ) => Promise<{ success: boolean; message: string }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearAuth: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [lastAuthCheck, setLastAuthCheck] = useState<number>(0);
  const navigate = useNavigate();

  // Set unauthorized callback for apiClient
  useEffect(() => {
    api.setOnUnauthorized(() => {
      logger.warn('Unauthorized access detected, clearing auth');
      setUser(null);
      api.clearToken();
      api.clearCache();
      navigate('/login');
    });
  }, [navigate]);

  // Check if user is authenticated on app load
  useEffect(() => {
    checkAuth();
  }, []);

  // Throttle auth checks to prevent excessive requests
  const shouldCheckAuth = () => {
    const now = Date.now();
    const timeSinceLastCheck = now - lastAuthCheck;
    return timeSinceLastCheck > 120000; // Only check every 2 minutes (increased from 30 seconds)
  };

  const checkAuth = async (forceCheck = false) => {
    // Throttle auth checks unless forced
    if (!forceCheck && !shouldCheckAuth()) {
      return;
    }

    try {
      setIsLoading(true);
      setLastAuthCheck(Date.now());
      
      // ALTERNATIVE APPROACH: Use JWT token if available (fallback for cookie issues)
      const authToken = localStorage.getItem('auth_token');
      const tokenType = localStorage.getItem('auth_token_type') || 'Bearer';
      
      const headers: HeadersInit = {
        'Cache-Control': 'max-age=120', // Cache for 2 minutes (increased from 30 seconds)
        'X-Requested-With': 'XMLHttpRequest',
      };
      
      // Add JWT token to Authorization header if available
      if (authToken) {
        headers['Authorization'] = `${tokenType} ${authToken}`;
      }
      
      // Use direct fetch to avoid CSRF token issues during auth check
      const response = await fetch('/api/v1/auth/check', {
        method: 'GET',
        credentials: 'include',
        headers,
      });

      // Check if response is empty or failed
      if (!response || response.status === 0) {
        logger.warn('Auth check: Empty response or network error. Backend may not be running.');
        // Don't clear user if we had one before - might be temporary network issue
        if (!user) {
          setUser(null);
          api.clearToken();
        }
        return;
      }

      // Check if response has content
      const contentType = response.headers.get('content-type');
      const hasJsonContent = contentType && contentType.includes('application/json');

      if (response.ok && hasJsonContent) {
        try {
          const text = await response.text();
          if (!text || text.trim() === '') {
            logger.warn('Auth check: Empty response body');
            if (!user) {
              setUser(null);
              api.clearToken();
            }
            return;
          }

          const data = JSON.parse(text);
          if (data.authenticated && data.user) {
            // Only clear cache if user data has actually changed
            const userChanged = !user || user.id !== data.user.id || user.username !== data.user.username;
            if (userChanged) {
              setUser(data.user);
              // Only clear cache when user actually changes
              api.clearCache();
            } else {
              setUser(data.user);
            }
          } else {
            // Only clear cache if we were previously authenticated
            if (user) {
              setUser(null);
              api.clearToken();
              api.clearCache();
              // Clear JWT token on logout
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_token_type');
            }
          }
        } catch (parseError) {
          logger.error('Auth check: Failed to parse response:', parseError);
          if (!user) {
            setUser(null);
            api.clearToken();
          }
        }
      } else {
        // Response not OK or not JSON
        logger.warn(`Auth check: Response not OK (${response.status}) or not JSON`);
        // Don't clear user immediately - might be temporary network issue or backend restart
        // Only clear if we get multiple consecutive failures
        if (response.status === 401 || response.status === 403) {
          // Real auth failure - clear user
          if (user) {
            setUser(null);
            api.clearToken();
            api.clearCache();
          }
        }
        // For other errors (500, 502, etc.), keep user logged in - might be temporary
      }
    } catch (error: any) {
      // Network errors, CORS errors, etc.
      logger.error('Auth check failed:', error);
      
      // Only clear user if it's a network error and we don't have a user
      // If we have a user, might be temporary network issue
      if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError') || error.name === 'TypeError') {
        logger.warn('Auth check: Network error - backend may not be running');
        if (!user) {
          setUser(null);
          api.clearToken();
        }
      } else {
        // Other errors - clear user
        setUser(null);
        api.clearToken();
      }
    } finally {
      setIsLoading(false);
      setIsInitialized(true);
    }
  };

  const login = async (
    username: string,
    password: string,
    rememberMe = false
  ): Promise<{ success: boolean; message: string }> => {
    try {
      setIsLoading(true);

      // Use direct fetch for login to avoid CSRF token issues
      let response: Response;
      try {
        response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: JSON.stringify({
            username,
            password,
            remember_me: rememberMe,
          }),
        });
      } catch (fetchError: any) {
        // Network error - backend not reachable
        logger.error('Login: Network error - backend may not be running', fetchError);
        return { 
          success: false, 
          message: 'Backend server is not responding. Please check if the server is running and try again.' 
        };
      }

      // Check if response is empty or failed
      if (!response || response.status === 0) {
        logger.error('Login: Empty response or network error. Backend may not be running.');
        return { 
          success: false, 
          message: 'Backend server is not responding. Please check if the server is running.' 
        };
      }

      // Check if response has content before parsing JSON
      const contentType = response.headers.get('content-type');
      const hasJsonContent = contentType && contentType.includes('application/json');
      
      let data: any = {};
      
      if (hasJsonContent) {
        try {
          const text = await response.text();
          if (!text || text.trim() === '') {
            logger.warn('Login: Empty response body');
            // Try to get error message from status
            if (response.status === 500) {
              return { 
                success: false, 
                message: 'Server error. Please check if backend is running and database is connected.' 
              };
            } else if (response.status === 401) {
              return { 
                success: false, 
                message: 'Invalid credentials. Please verify your username and password.' 
              };
            }
            return { 
              success: false, 
              message: `Server returned empty response (${response.status}). Please check if backend is running.` 
            };
          }
          data = JSON.parse(text);
        } catch (parseError) {
          logger.error('Failed to parse response:', parseError);
          // If response is not OK and we can't parse JSON, return error
          if (!response.ok) {
            if (response.status === 500) {
              return { 
                success: false, 
                message: 'Server error. Please check if backend is running and database is connected.' 
              };
            } else if (response.status === 401) {
              return { 
                success: false, 
                message: 'Invalid credentials. Please verify your username and password.' 
              };
            }
            return { 
              success: false, 
              message: `Server error (${response.status}). Please check if backend is running.` 
            };
          }
        }
      } else if (!response.ok) {
        // Response not OK and not JSON
        if (response.status === 500) {
          return { 
            success: false, 
            message: 'Server error. Please check if backend is running and database is connected.' 
          };
        } else if (response.status === 401) {
          return { 
            success: false, 
            message: 'Invalid credentials. Please verify your username and password.' 
          };
        }
        return { 
          success: false, 
          message: `Server error (${response.status}). Please check if backend is running.` 
        };
      }

      if (response.ok && data.user) {
        setUser(data.user);
        
        // ALTERNATIVE APPROACH: Store JWT token if provided (fallback for cookie issues)
        if (data.token) {
          localStorage.setItem('auth_token', data.token);
          localStorage.setItem('auth_token_type', data.token_type || 'Bearer');
          logger.info('JWT token stored for authentication');
        }
        
        // Clear cache and get fresh CSRF token after successful login
        api.clearCache();
        await api.refreshSession();
        return { success: true, message: data.message || 'Login successful' };
      } else {
        // Handle different error scenarios
        if (response.status === 500) {
          return { 
            success: false, 
            message: data.error || data.message || 'Server error. Please check if backend is running and database is connected.' 
          };
        } else if (response.status === 401) {
          return { 
            success: false, 
            message: data.error || data.message || 'Invalid credentials. Please verify your username and password.' 
          };
        } else {
          return { 
            success: false, 
            message: data.error || data.message || `Login failed (${response.status})` 
          };
        }
      }
    } catch (error: any) {
      logger.error('Login error:', error);
      
      // Network errors
      if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError') || error.name === 'TypeError') {
        return { 
          success: false, 
          message: 'Network error. Backend server may not be running. Please check server connection.' 
        };
      }
      
      // JSON parse errors
      if (error instanceof SyntaxError && error.message.includes('JSON')) {
        return { 
          success: false, 
          message: 'Server returned invalid response. Please check if backend is running.' 
        };
      }
      
      return { 
        success: false, 
        message: error.message || 'Network error. Please try again.' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Use direct fetch for logout
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      api.clearToken(); // Clear CSRF token and auth_token
      api.clearCache(); // Clear all cached data
      // Explicitly clear JWT token
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_token_type');
      setUser(null);
      navigate('/login');
    }
  };

  const clearAuth = () => {
    setUser(null);
    api.clearToken();
    api.clearCache();
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading: isLoading || !isInitialized,
    login,
    logout,
    checkAuth,
    clearAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
