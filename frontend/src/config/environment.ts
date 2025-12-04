// Environment configuration
interface EnvironmentConfig {
  apiBaseUrl: string;
  environment: 'development' | 'production' | 'test';
  debug: boolean;
  version: string;
  buildTime: string;
}

// Get environment variables with fallbacks
const getEnvVar = (key: string, defaultValue: string = ''): string => {
  return import.meta.env[key] || defaultValue;
};

// Environment configuration
export const config: EnvironmentConfig = {
  apiBaseUrl: getEnvVar('VITE_API_BASE_URL', ''),
  environment: (getEnvVar('VITE_ENVIRONMENT', 'development') as 'development' | 'production' | 'test'),
  debug: getEnvVar('VITE_DEBUG', 'false') === 'true',
  version: getEnvVar('VITE_APP_VERSION', '1.0.0'),
  buildTime: getEnvVar('VITE_BUILD_TIME', new Date().toISOString()),
};

// Helper functions
export const isDevelopment = (): boolean => config.environment === 'development';
export const isProduction = (): boolean => config.environment === 'production';
export const isTest = (): boolean => config.environment === 'test';

// API configuration
export const apiConfig = {
  baseURL: config.apiBaseUrl || (isDevelopment() ? 'http://localhost:5000' : ''),
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// Feature flags
export const featureFlags = {
  enableDebugMode: config.debug,
  enableAnalytics: isProduction(),
  enableErrorReporting: isProduction(),
  enablePerformanceMonitoring: isProduction(),
};

// Logging configuration
export const loggingConfig = {
  level: isDevelopment() ? 'debug' : 'info',
  enableConsoleLogs: isDevelopment(),
  enableNetworkLogs: isDevelopment(),
};

export default config;
