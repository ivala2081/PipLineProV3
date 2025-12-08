/**
 * Logger Service
 * Production'da console.log'ları disable eder, development'ta gösterir
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class Logger {
  private isDevelopment = import.meta.env.DEV;
  private isProduction = import.meta.env.PROD;

  private shouldLog(level: LogLevel): boolean {
    if (this.isProduction) {
      // Production'da sadece error ve warn göster
      return level === 'error' || level === 'warn';
    }
    return true;
  }

  debug(...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.debug('[DEBUG]', ...args);
    }
  }

  info(...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info('[INFO]', ...args);
    }
  }

  warn(...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn('[WARN]', ...args);
    }
  }

  error(...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error('[ERROR]', ...args);
    }
  }

  // Dashboard specific loggers
  dashboard(message: string, data?: any): void {
    if (this.isDevelopment) {

    }
  }

  api(endpoint: string, method: string, data?: any): void {
    if (this.isDevelopment) {

    }
  }

  performance(metric: string, value: number, unit: string = 'ms'): void {
    if (this.isDevelopment) {

    }
  }

  // Clients page specific logger - sadece development modda
  clients(message: string, data?: any): void {
    if (this.isDevelopment) {

    }
  }

  // Transaction related logger - sadece development modda
  transaction(message: string, data?: any): void {
    if (this.isDevelopment) {

    }
  }

  // Health check logger - sadece development modda
  health(message: string, data?: any): void {
    if (this.isDevelopment) {

    }
  }
}

// Export singleton instance
export const logger = new Logger();
export default logger;
