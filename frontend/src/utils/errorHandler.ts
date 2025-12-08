/**
 * Standardized Error Handling for PipLinePro Frontend
 * Provides consistent error handling patterns across the application
 */

export interface ErrorDetails {
  message: string;
  code?: string;
  status?: number;
  timestamp: string;
  context?: Record<string, any>;
}

export interface ApiError {
  error: string;
  message: string;
  code?: string;
  details?: any;
}

export class PipLineError extends Error {
  public code?: string;
  public status?: number;
  public context?: Record<string, any>;

  constructor(message: string, code?: string, status?: number, context?: Record<string, any>) {
    super(message);
    this.name = 'PipLineError';
    this.code = code;
    this.status = status;
    this.context = context;
  }
}

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorLog: ErrorDetails[] = [];
  private maxLogSize = 100;

  private constructor() {}

  public static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * Handle API errors consistently
   */
  public handleApiError(error: any, context?: string): PipLineError {
    let errorMessage = 'An unexpected error occurred';
    let errorCode = 'UNKNOWN_ERROR';
    let status = 500;

    if (error instanceof PipLineError) {
      return error;
    }

    if (error.response) {
      // API response error
      const apiError: ApiError = error.response.data || {};
      errorMessage = apiError.message || apiError.error || 'API request failed';
      errorCode = apiError.code || `HTTP_${error.response.status}`;
      status = error.response.status;
    } else if (error.request) {
      // Network error
      errorMessage = 'Network error - please check your connection';
      errorCode = 'NETWORK_ERROR';
      status = 0;
    } else if (error.message) {
      // Generic error
      errorMessage = error.message;
      errorCode = 'GENERIC_ERROR';
    }

    const pipLineError = new PipLineError(errorMessage, errorCode, status, {
      originalError: error,
      context,
      timestamp: new Date().toISOString()
    });

    this.logError(pipLineError);
    return pipLineError;
  }

  /**
   * Handle component errors
   */
  public handleComponentError(error: Error, errorInfo: any, componentName?: string): void {
    const pipLineError = new PipLineError(
      error.message,
      'COMPONENT_ERROR',
      0,
      {
        componentName,
        errorInfo,
        stack: error.stack,
        timestamp: new Date().toISOString()
      }
    );

    this.logError(pipLineError);
  }

  /**
   * Handle validation errors
   */
  public handleValidationError(message: string, field?: string): PipLineError {
    const pipLineError = new PipLineError(
      message,
      'VALIDATION_ERROR',
      400,
      {
        field,
        timestamp: new Date().toISOString()
      }
    );

    this.logError(pipLineError);
    return pipLineError;
  }

  /**
   * Handle authentication errors
   */
  public handleAuthError(message: string = 'Authentication required'): PipLineError {
    const pipLineError = new PipLineError(
      message,
      'AUTH_ERROR',
      401,
      {
        timestamp: new Date().toISOString()
      }
    );

    this.logError(pipLineError);
    return pipLineError;
  }

  /**
   * Handle permission errors
   */
  public handlePermissionError(message: string = 'Insufficient permissions'): PipLineError {
    const pipLineError = new PipLineError(
      message,
      'PERMISSION_ERROR',
      403,
      {
        timestamp: new Date().toISOString()
      }
    );

    this.logError(pipLineError);
    return pipLineError;
  }

  /**
   * Log error details
   */
  private logError(error: PipLineError): void {
    const errorDetails: ErrorDetails = {
      message: error.message,
      code: error.code,
      status: error.status,
      timestamp: new Date().toISOString(),
      context: error.context
    };

    this.errorLog.unshift(errorDetails);

    // Keep only the most recent errors
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }

    // In development, also log to console
    if (process.env.NODE_ENV === 'development') {
      console.error('PipLineError:', errorDetails);
    }
  }

  /**
   * Get error log for debugging
   */
  public getErrorLog(): ErrorDetails[] {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  public clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Get user-friendly error message
   */
  public getUserFriendlyMessage(error: PipLineError): string {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'Please check your internet connection and try again.';
      case 'AUTH_ERROR':
        return 'Please log in to continue.';
      case 'PERMISSION_ERROR':
        return 'You do not have permission to perform this action.';
      case 'VALIDATION_ERROR':
        return error.message;
      case 'COMPONENT_ERROR':
        return 'Something went wrong. Please refresh the page.';
      default:
        return error.message || 'An unexpected error occurred. Please try again.';
    }
  }

  /**
   * Check if error is retryable
   */
  public isRetryable(error: PipLineError): boolean {
    return error.code === 'NETWORK_ERROR' || 
           (error.status && error.status >= 500) ||
           error.status === 0;
  }

  /**
   * Get retry delay in milliseconds
   */
  public getRetryDelay(attempt: number): number {
    return Math.min(1000 * Math.pow(2, attempt), 10000); // Exponential backoff, max 10s
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();

// Export utility functions
export const handleApiError = (error: any, context?: string) => 
  errorHandler.handleApiError(error, context);

export const handleComponentError = (error: Error, errorInfo: any, componentName?: string) => 
  errorHandler.handleComponentError(error, errorInfo, componentName);

export const handleValidationError = (message: string, field?: string) => 
  errorHandler.handleValidationError(message, field);

export const handleAuthError = (message?: string) => 
  errorHandler.handleAuthError(message);

export const handlePermissionError = (message?: string) => 
  errorHandler.handlePermissionError(message);

export const getUserFriendlyMessage = (error: PipLineError) => 
  errorHandler.getUserFriendlyMessage(error);

export const isRetryable = (error: PipLineError) => 
  errorHandler.isRetryable(error);

export const getRetryDelay = (attempt: number) => 
  errorHandler.getRetryDelay(attempt);
