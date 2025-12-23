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
    // Map technical error codes to user-friendly messages
    const errorMessages: Record<string, string> = {
      'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection and try again.',
      'HTTP_401': 'Your session has expired. Please log in again.',
      'HTTP_403': 'You do not have permission to perform this action.',
      'HTTP_404': 'The requested resource was not found.',
      'HTTP_500': 'A server error occurred. Please try again later.',
      'HTTP_502': 'The server is temporarily unavailable. Please try again in a few moments.',
      'HTTP_503': 'The service is temporarily unavailable. Please try again later.',
      'HTTP_504': 'The request took too long. Please try again.',
      'VALIDATION_ERROR': 'Please check your input and try again.',
      'AUTH_ERROR': 'Authentication failed. Please log in again.',
      'PERMISSION_ERROR': 'You do not have permission to perform this action.',
      'TIMEOUT_ERROR': 'The request took too long. Please try again.',
      'COMPONENT_ERROR': 'Something went wrong. Please refresh the page.',
      'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.',
    };

    // Check for specific error patterns in message
    const message = error.message || '';
    
    // Network-related errors
    if (message.includes('Failed to fetch') || message.includes('NetworkError') || message.includes('network')) {
      return 'Connection problem. Please check your internet connection and try again.';
    }
    
    // Timeout errors
    if (message.includes('timeout') || message.includes('Timeout')) {
      return 'The request took too long. Please try again.';
    }
    
    // Validation errors - return as-is if already user-friendly
    if (message.includes('validation') || message.includes('invalid') || message.includes('required')) {
      // If it's a simple validation message, return it; otherwise provide generic
      if (message.length < 100 && !message.includes('Error') && !message.includes('Exception')) {
        return message;
      }
      return 'Please check your input and try again.';
    }
    
    // Database errors (user-friendly)
    if (message.includes('database') || message.includes('SQL') || message.includes('constraint')) {
      return 'A data error occurred. Please check your input or contact support if the problem persists.';
    }
    
    // If we have a mapped error code, use it
    if (error.code && errorMessages[error.code]) {
      return errorMessages[error.code];
    }
    
    // If status code is available, map it
    if (error.status) {
      const statusMessage = errorMessages[`HTTP_${error.status}`];
      if (statusMessage) {
        return statusMessage;
      }
    }

    // Return the original message if it's already user-friendly, otherwise return generic message
    const isTechnical = /(error|exception|failed|undefined|null|NaN|stack|trace)/i.test(message);
    if (!isTechnical && message.length < 200 && message.trim().length > 0) {
      return message;
    }
    
    return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
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
