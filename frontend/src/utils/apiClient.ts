/**
 * API Client with Retry, Timeout, and Error Handling
 * Centralized API request handling with retry mechanism
 */

import { logger } from './logger';

export interface ApiClientOptions {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  retryOn?: number[]; // HTTP status codes to retry on
}

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
  ok: boolean; // HTTP response ok status
}

export class ApiClient {
  private baseUrl: string;
  private defaultOptions: Required<ApiClientOptions>;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private onUnauthorizedCallback: (() => void) | null = null;
  private unauthorizedAttempts: Map<string, number> = new Map(); // Track 401/403 attempts per endpoint
  private readonly MAX_UNAUTHORIZED_ATTEMPTS = 2; // Allow 2 attempts before redirecting
  private clientLogThrottle: Map<string, number> = new Map(); // Throttle client-log calls
  private readonly CLIENT_LOG_THROTTLE_MS = 2000; // Only log once per 2 seconds per location

  constructor(baseUrl: string = '/api/v1', options: ApiClientOptions = {}) {
    this.baseUrl = baseUrl;
    this.defaultOptions = {
      timeout: 15000, // 15 seconds
      retries: 3,
      retryDelay: 1000, // 1 second
      retryOn: [408, 429, 500, 502, 503, 504],
      ...options,
    };
  }

  /**
   * Set callback for unauthorized (401/403) errors
   */
  setOnUnauthorized(callback: () => void) {
    this.onUnauthorizedCallback = callback;
  }

  /**
   * Throttled client log - only log once per CLIENT_LOG_THROTTLE_MS per location
   */
  private sendClientLog(location: string, message: string, data: any): void {
    if (!import.meta.env.DEV) return; // Only in development
    
    const now = Date.now();
    const lastCall = this.clientLogThrottle.get(location) || 0;
    
    // Throttle: only send if enough time has passed
    if (now - lastCall < this.CLIENT_LOG_THROTTLE_MS) {
      return; // Skip this log call
    }
    
    // Update throttle timestamp
    this.clientLogThrottle.set(location, now);
    
    // Send log (fire and forget)
    fetch('/api/v1/monitoring/client-log', {
      method: 'POST',
      keepalive: true,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location,
        message,
        data,
        timestamp: now,
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId: 'B'
      })
    }).catch(() => {}); // Ignore errors
  }

  /**
   * Retry mechanism with exponential backoff
   */
  private async retry<T>(
    fn: () => Promise<T>,
    options: Required<ApiClientOptions>,
    attempt: number = 0,
  ): Promise<T> {
    try {
      return await fn();
    } catch (error: any) {
      const shouldRetry =
        attempt < options.retries &&
        (options.retryOn.includes(error.status) || error.name === 'AbortError' || error.name === 'NetworkError');

      if (shouldRetry) {
        const delay = options.retryDelay * Math.pow(2, attempt); // Exponential backoff
        logger.warn(`Retry attempt ${attempt + 1}/${options.retries} after ${delay}ms`, error);

        await new Promise((resolve) => setTimeout(resolve, delay));
        return this.retry(fn, options, attempt + 1);
      }

      throw error;
    }
  }

  /**
   * Create abort controller with timeout
   */
  private createTimeoutController(timeout: number): AbortController {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), timeout);
    return controller;
  }

  /**
   * Handle 401/403 errors with retry logic - don't redirect immediately
   */
  private handleUnauthorized(url: string, status: number): void {
    const attempts = this.unauthorizedAttempts.get(url) || 0;
    
    // İlk denemede hemen redirect etme - CSRF token veya geçici hata olabilir
    if (attempts < this.MAX_UNAUTHORIZED_ATTEMPTS) {
      this.unauthorizedAttempts.set(url, attempts + 1);
      logger.warn(`Unauthorized response (${status}) from ${url} - attempt ${attempts + 1}/${this.MAX_UNAUTHORIZED_ATTEMPTS}. May be temporary.`);
      
      // Clear attempts after 10 seconds to allow retries
      setTimeout(() => {
        this.unauthorizedAttempts.delete(url);
      }, 10000);
    } else {
      // Multiple consecutive 401/403 - likely real auth failure
      logger.error(`Multiple unauthorized responses (${status}) from ${url}, redirecting to login`);
      this.unauthorizedAttempts.delete(url);
      
      if (this.onUnauthorizedCallback) {
        this.onUnauthorizedCallback();
      } else if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  }

  /**
   * Handle API errors with proper error messages
   */
  private handleError(error: any, url: string): Error {
    if (error.name === 'AbortError') {
      return new Error('Request timeout. Please try again.');
    }

    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      return new Error('Connection error. Please check your internet connection and try again.');
    }

    if (error.status === 401 || error.status === 403) {
      // Use the new resilient handler
      this.handleUnauthorized(url, error.status);
      return new Error('Your session has expired. Please log in again.');
    }

    if (error.status >= 500) {
      if (error.status === 502) {
        return new Error('Server is temporarily unavailable. Please try again in a few moments.');
      }
      if (error.status === 503) {
        return new Error('Service is temporarily unavailable. Please try again later.');
      }
      if (error.status === 504) {
        return new Error('Request took too long. Please try again.');
      }
      return new Error('Server error. Please try again later or contact support if the problem persists.');
    }

    if (error.status === 404) {
      return new Error('The requested resource was not found.');
    }
    
    if (error.status === 400) {
      // Try to extract validation error message
      const errorData = error.data || error.response?.data || {};
      const errorMessage = errorData.message || errorData.error || errorData.detail;
      if (errorMessage) {
        return new Error(errorMessage);
      }
      return new Error('Invalid request. Please check your input and try again.');
    }

    if (error.status === 422) {
      const errorData = error.data || error.response?.data || {};
      const errorMessage = errorData.message || errorData.error || errorData.detail;
      if (errorMessage) {
        return new Error(errorMessage);
      }
      return new Error('Validation error. Please check your input and try again.');
    }

    return error instanceof Error ? error : new Error(error.message || 'An unexpected error occurred. Please try again.');
  }

  /**
   * Make GET request
   */
  async get<T>(
    endpoint: string,
    options: ApiClientOptions = {},
  ): Promise<ApiResponse<T>> {
    const opts = { ...this.defaultOptions, ...options };
    const url = `${this.baseUrl}${endpoint}`;

    return this.retry(async () => {
      const controller = this.createTimeoutController(opts.timeout);

      try {
        // #region agent log (dev only - throttled)
        this.sendClientLog('apiClient.ts:get:start', 'API GET start', {
          url,
          timeout: opts.timeout,
          retries: opts.retries,
          hasCsrf: !!localStorage.getItem('csrf_token')
        });
        // #endregion
        // ALTERNATIVE APPROACH: Add JWT token to Authorization header if available
        const authToken = localStorage.getItem('auth_token');
        const tokenType = localStorage.getItem('auth_token_type') || 'Bearer';
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };
        
        // Add JWT token to Authorization header if available (fallback for cookie issues)
        if (authToken) {
          headers['Authorization'] = `${tokenType} ${authToken}`;
        }
        
        const response = await fetch(url, {
          method: 'GET',
          credentials: 'include',
          headers,
          signal: controller.signal,
        });

        if (!response.ok) {
          // 401/403 hatalarında esnek yaklaşım - hemen redirect etme
          if (response.status === 401 || response.status === 403) {
            this.handleUnauthorized(url, response.status);
          }
          // #region agent log (dev only - throttled)
          this.sendClientLog('apiClient.ts:get:non-ok', 'API GET non-ok response', {
            url,
            status: response.status,
            ok: response.ok
          });
          // #endregion
          const error: any = new Error(`HTTP error! status: ${response.status}`);
          error.status = response.status;
          throw error;
        } else {
          // Successful response - clear unauthorized attempts counter
          this.unauthorizedAttempts.delete(url);
        }

        const text = await response.text();
        if (!text || text.trim() === '') {
          // Empty response - might be backend issue
          logger.warn(`Empty response from ${url}`);
          throw new Error('Empty response from server');
        }

        let data;
        try {
          data = JSON.parse(text);
        } catch (parseError) {
          logger.error(`Failed to parse JSON from ${url}:`, parseError);
          throw new Error('Invalid JSON response from server');
        }

        return {
          data,
          status: response.status,
          headers: response.headers,
          ok: response.ok, // Include ok status for compatibility
        };
      } catch (error: any) {
        // #region agent log (dev only - throttled)
        this.sendClientLog('apiClient.ts:get:error', 'API GET threw', {
          url,
          errorMessage: error?.message || String(error),
          name: error?.name,
          status: error?.status
        });
        // #endregion
        throw this.handleError(error, url);
      }
    }, opts);
  }

  /**
   * Make POST request
   */
  async post<T>(
    endpoint: string,
    body: any,
    options: ApiClientOptions = {},
  ): Promise<ApiResponse<T>> {
    const opts = { ...this.defaultOptions, ...options };
    const url = `${this.baseUrl}${endpoint}`;

    return this.retry(async () => {
      const controller = this.createTimeoutController(opts.timeout);

      try {
        // CSRF token'i localStorage'dan al
        const csrfToken = localStorage.getItem('csrf_token');
        // #region agent log (dev only - throttled)
        this.sendClientLog('apiClient.ts:post:start', 'API POST start', {
          url,
          timeout: opts.timeout,
          retries: opts.retries,
          hasCsrf: !!csrfToken,
          bodyType: typeof body
        });
        // #endregion
        
        // ALTERNATIVE APPROACH: Add JWT token to Authorization header if available
        const authToken = localStorage.getItem('auth_token');
        const tokenType = localStorage.getItem('auth_token_type') || 'Bearer';
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        };
        
        // Add JWT token to Authorization header if available (fallback for cookie issues)
        if (authToken) {
          headers['Authorization'] = `${tokenType} ${authToken}`;
        }
        
        const response = await fetch(url, {
          method: 'POST',
          credentials: 'include',
          headers,
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        const text = await response.text();
        let data;
        
        if (text && text.trim() !== '') {
          try {
            data = JSON.parse(text);
          } catch (parseError) {
            logger.error(`Failed to parse JSON from ${url}:`, parseError);
            data = { error: text };
          }
        } else {
          data = {};
        }

        if (!response.ok) {
          // 401/403 hatalarında esnek yaklaşım - hemen redirect etme
          if (response.status === 401 || response.status === 403) {
            this.handleUnauthorized(url, response.status);
          }
          // #region agent log (dev only - throttled)
          this.sendClientLog('apiClient.ts:post:non-ok', 'API POST non-ok response', {
            url,
            status: response.status,
            ok: response.ok
          });
          // #endregion
          
          // Return error response with data so caller can access error message
          return {
            data,
            status: response.status,
            headers: response.headers,
            ok: false,
          };
        } else {
          // Successful response - clear unauthorized attempts counter
          this.unauthorizedAttempts.delete(url);
        }

        return {
          data,
          status: response.status,
          headers: response.headers,
          ok: response.ok, // Use response.ok which correctly handles 2xx status codes including 201
        };
      } catch (error: any) {
        // #region agent log (dev only - throttled)
        this.sendClientLog('apiClient.ts:post:error', 'API POST threw', {
          url,
          errorMessage: error?.message || String(error),
          name: error?.name,
          status: error?.status
        });
        // #endregion
        throw this.handleError(error, url);
      }
    }, opts);
  }

  /**
   * Make PUT request
   */
  async put<T>(
    endpoint: string,
    body: any,
    options: ApiClientOptions = {},
  ): Promise<ApiResponse<T>> {
    const opts = { ...this.defaultOptions, ...options };
    const url = `${this.baseUrl}${endpoint}`;

    return this.retry(async () => {
      const controller = this.createTimeoutController(opts.timeout);

      try {
        // CSRF token'i localStorage'dan al
        const csrfToken = localStorage.getItem('csrf_token');
        // ALTERNATIVE APPROACH: Add JWT token to Authorization header if available
        const authToken = localStorage.getItem('auth_token');
        const tokenType = localStorage.getItem('auth_token_type') || 'Bearer';
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        };
        
        // Add JWT token to Authorization header if available (fallback for cookie issues)
        if (authToken) {
          headers['Authorization'] = `${tokenType} ${authToken}`;
        }
        
        const response = await fetch(url, {
          method: 'PUT',
          credentials: 'include',
          headers,
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (!response.ok) {
          // 401/403 hatalarında esnek yaklaşım - hemen redirect etme
          if (response.status === 401 || response.status === 403) {
            this.handleUnauthorized(url, response.status);
          }
          const error: any = new Error(`HTTP error! status: ${response.status}`);
          error.status = response.status;
          throw error;
        } else {
          // Successful response - clear unauthorized attempts counter
          this.unauthorizedAttempts.delete(url);
        }

        const text = await response.text();
        if (!text || text.trim() === '') {
          // Empty response - might be backend issue
          logger.warn(`Empty response from ${url}`);
          throw new Error('Empty response from server');
        }

        let data;
        try {
          data = JSON.parse(text);
        } catch (parseError) {
          logger.error(`Failed to parse JSON from ${url}:`, parseError);
          throw new Error('Invalid JSON response from server');
        }

        return {
          data,
          status: response.status,
          headers: response.headers,
          ok: response.ok, // Include ok status for compatibility
        };
      } catch (error: any) {
        throw this.handleError(error, url);
      }
    }, opts);
  }

  /**
   * Make DELETE request
   */
  async delete<T>(
    endpoint: string,
    body?: any,
    options: ApiClientOptions = {},
  ): Promise<ApiResponse<T>> {
    const opts = { ...this.defaultOptions, ...options };
    const url = `${this.baseUrl}${endpoint}`;

    return this.retry(async () => {
      const controller = this.createTimeoutController(opts.timeout);

      try {
        // CSRF token'i localStorage'dan al
        const csrfToken = localStorage.getItem('csrf_token');
        // ALTERNATIVE APPROACH: Add JWT token to Authorization header if available
        const authToken = localStorage.getItem('auth_token');
        const tokenType = localStorage.getItem('auth_token_type') || 'Bearer';
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        };
        
        // Add JWT token to Authorization header if available (fallback for cookie issues)
        if (authToken) {
          headers['Authorization'] = `${tokenType} ${authToken}`;
        }
        
        const response = await fetch(url, {
          method: 'DELETE',
          credentials: 'include',
          headers,
          ...(body ? { body: JSON.stringify(body) } : {}),
          signal: controller.signal,
        });

        if (!response.ok) {
          // 401/403 hatalarında esnek yaklaşım - hemen redirect etme
          if (response.status === 401 || response.status === 403) {
            this.handleUnauthorized(url, response.status);
          }
          const error: any = new Error(`HTTP error! status: ${response.status}`);
          error.status = response.status;
          throw error;
        } else {
          // Successful response - clear unauthorized attempts counter
          this.unauthorizedAttempts.delete(url);
        }

        const text = await response.text();
        if (!text || text.trim() === '') {
          return {
            data: {} as T,
            status: response.status,
            headers: response.headers,
            ok: response.ok, // Include ok status for compatibility
          };
        }

        const data = JSON.parse(text);

        return {
          data,
          status: response.status,
          headers: response.headers,
          ok: response.ok, // Include ok status for compatibility
        };
      } catch (error: any) {
        throw this.handleError(error, url);
      }
    }, opts);
  }

  /**
   * Parse response data from ApiResponse
   * Handles both new standardized format {data, error, meta} and legacy formats
   */
  parseResponse<T>(response: ApiResponse<T>): T {
    const responseData = response.data as any;
    
    // New standardized format: {data, error, meta}
    if (responseData && typeof responseData === 'object') {
      // Check if it's the new format
      if ('data' in responseData || 'error' in responseData || 'meta' in responseData) {
        // If error exists, throw it
        if (responseData.error) {
          const error = new Error(responseData.error.message || 'API error');
          (error as any).code = responseData.error.code;
          (error as any).details = responseData.error.details;
          throw error;
        }
        // Return data from new format
        return (responseData.data !== undefined ? responseData.data : responseData) as T;
      }
    }
    
    // Legacy format: return data directly
    return response.data as T;
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    try {
      // localStorage'dan token'ları temizle
      localStorage.removeItem('auth_token');
      localStorage.removeItem('csrf_token');
      localStorage.removeItem('session_token');
      logger.info('Authentication tokens cleared');
    } catch (error) {
      logger.error('Error clearing tokens:', error);
    }
  }

  /**
   * Clear all cache
   */
  clearCache(): void {
    try {
      this.cache.clear();
      // localStorage'dan cache'leri temizle
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
        if (key.startsWith('api_cache_')) {
          localStorage.removeItem(key);
        }
      });
      logger.info('Cache cleared');
    } catch (error) {
      logger.error('Error clearing cache:', error);
    }
  }

  /**
   * Clear cache for specific URL
   */
  clearCacheForUrl(urlPattern: string): void {
    try {
      // Memory cache'den temizle
      const keysToDelete: string[] = [];
      this.cache.forEach((_, key) => {
        if (key.includes(urlPattern)) {
          keysToDelete.push(key);
        }
      });
      keysToDelete.forEach((key) => this.cache.delete(key));

      // localStorage'dan temizle
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
        if (key.startsWith('api_cache_') && key.includes(urlPattern)) {
          localStorage.removeItem(key);
        }
      });
      logger.info(`Cache cleared for URL pattern: ${urlPattern}`);
    } catch (error) {
      logger.error('Error clearing cache for URL:', error);
    }
  }

  /**
   * Make batched request (wrapper for get method for compatibility)
   * The batchKey parameter is ignored but kept for API compatibility
   */
  async makeBatchedRequest<T>(
    endpoint: string,
    options: ApiClientOptions = {},
    batchKey?: string
  ): Promise<T> {
    const response = await this.get<T>(endpoint, options);
    return this.parseResponse(response);
  }

  /**
   * Refresh session and get new CSRF token
   */
  async refreshSession(): Promise<boolean> {
    try {
      logger.info('Refreshing session...');
      const response = await this.get<{ csrf_token?: string; success?: boolean }>('/auth/csrf-token');
      const data = this.parseResponse(response);
      
      if (data.csrf_token) {
        localStorage.setItem('csrf_token', data.csrf_token);
        logger.info('Session refreshed successfully');
        return true;
      }
      
      logger.warn('Session refresh returned no CSRF token');
      return false;
    } catch (error) {
      logger.error('Error refreshing session:', error);
      return false;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
// Alias for backward compatibility
export const api = apiClient;
export default apiClient;
