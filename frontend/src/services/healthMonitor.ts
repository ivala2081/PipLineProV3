/**
 * Frontend Health Monitoring Service
 * Provides real-time monitoring and automatic recovery for frontend issues
 */

import { api } from '../utils/apiClient';

interface HealthStatus {
  backend: boolean;
  frontend: boolean;
  session: boolean;
  csrf: boolean;
  timestamp: string;
}

interface HealthCheckResult {
  status: HealthStatus;
  issues: string[];
  recommendations: string[];
}

class HealthMonitor {
  private isMonitoring = false;
  private checkInterval: number | null = null;
  private lastHealthStatus: HealthStatus | null = null;

  /**
   * Start health monitoring
   */
  public startMonitoring(intervalMs: number = 30000): void {
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;

    // Run initial health check
    this.performHealthCheck();

    // Set up periodic health checks
    this.checkInterval = setInterval(() => {
      this.performHealthCheck();
    }, intervalMs) as unknown as number;
  }

  /**
   * Stop health monitoring
   */
  public stopMonitoring(): void {
    if (!this.isMonitoring) {
      return;
    }

    this.isMonitoring = false;

    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  /**
   * Perform a comprehensive health check
   */
  public async performHealthCheck(): Promise<HealthCheckResult> {
    const issues: string[] = [];
    const recommendations: string[] = [];

    const healthStatus: HealthStatus = {
      backend: false,
      frontend: false,
      session: false,
      csrf: false,
      timestamp: new Date().toISOString(),
    };

    try {
      // Check backend health
      try {
        const response = await api.get('/health');
        healthStatus.backend = response.ok;
        if (!response.ok) {
          issues.push('Backend is not responding');
          recommendations.push('Check if the Flask server is running');
        }
      } catch (error) {
        issues.push('Cannot connect to backend');
        recommendations.push('Restart the Flask server');
      }

      // Check frontend proxy
      try {
        const response = await fetch('/api/v1/health');
        healthStatus.frontend = response.ok;
        if (!response.ok) {
          issues.push('Frontend proxy is not working');
          recommendations.push('Check Vite configuration and restart frontend');
        }
      } catch (error) {
        issues.push('Frontend proxy connection failed');
        recommendations.push('Restart the frontend development server');
      }

      // Check session
      try {
        const response = await api.get('/auth/check');
        healthStatus.session = response.ok;
        if (!response.ok) {
          issues.push('Session is invalid or expired');
          recommendations.push('User should log in again');
        }
      } catch (error) {
        issues.push('Session check failed');
        recommendations.push('Clear browser cookies and log in again');
      }

      // Check CSRF token
      try {
        const response = await api.get('/auth/csrf-token');
        if (response.ok) {
          const data: any = api.parseResponse(response);
          healthStatus.csrf = !!data.csrf_token;
          if (!data.csrf_token) {
            issues.push('CSRF token generation failed');
            recommendations.push('Refresh the page to get a new token');
          }
        } else {
          issues.push('CSRF token endpoint not responding');
          recommendations.push('Check backend CSRF configuration');
        }
      } catch (error) {
        issues.push('CSRF token check failed');
        recommendations.push('Refresh the page and try again');
      }
    } catch (error) {
      console.error('💥 Health check failed:', error);
      issues.push('Health check process failed');
      recommendations.push('Check browser console for errors');
    }

    // Log health status
    this.logHealthStatus(healthStatus, issues, recommendations);

    // Store last health status
    this.lastHealthStatus = healthStatus;

    return {
      status: healthStatus,
      issues,
      recommendations,
    };
  }

  /**
   * Log health status with detailed information
   */
  private logHealthStatus(
    status: HealthStatus,
    issues: string[],
    recommendations: string[]
  ): void {
    const allHealthy =
      Object.values(status).every(Boolean) && issues.length === 0;

    // Sadece sorun varsa log at (development modda bile)
    if (!allHealthy) {
      console.warn('⚠️ Health check issues detected:', {
        status,
        issues,
        recommendations,
      });
    }
  }

  /**
   * Get last health status
   */
  public getLastHealthStatus(): HealthStatus | null {
    return this.lastHealthStatus;
  }

  /**
   * Check if system is healthy
   */
  public isHealthy(): boolean {
    if (!this.lastHealthStatus) {
      return false;
    }

    return Object.values(this.lastHealthStatus).every(Boolean);
  }

  /**
   * Force refresh session and CSRF token
   */
  public async refreshSession(): Promise<boolean> {

    try {
      // Clear existing tokens
      api.clearToken();

      // Get new CSRF token
      const response = await api.get('/api/v1/auth/csrf-token');
      if (response.ok) {

        return true;
      } else {
        console.error('❌ Failed to refresh session');
        return false;
      }
    } catch (error) {
      console.error('💥 Session refresh failed:', error);
      return false;
    }
  }

  /**
   * Test transaction creation endpoint
   */
  public async testTransactionCreation(): Promise<boolean> {

    try {
      // Prepare test data
      const testData = {
        client_name: 'HEALTH CHECK TEST',
        amount: '1.00',
        currency: 'TL',
        payment_method: 'BANKA',
        category: 'DEP',
        psp: '#61',
        iban: 'IBAN',
        company_order: 'TEST COMPANY',
        date: new Date().toISOString().split('T')[0],
        notes: 'Health check test transaction',
      };

      const response = await api.post('/transactions', testData);

      if (response.ok) {
        const data: any = api.parseResponse(response);
        if (data.success) {

          return true;
        } else {
          console.error('❌ Transaction creation test failed:', data.error);
          return false;
        }
      } else {
        console.error('❌ Transaction creation endpoint not responding');
        return false;
      }
    } catch (error) {
      console.error('💥 Transaction creation test failed:', error);
      return false;
    }
  }
}

// Create singleton instance
export const healthMonitor = new HealthMonitor();

// Auto-start monitoring when module is imported
if (typeof window !== 'undefined') {
  // Only start in browser environment
  setTimeout(() => {
    healthMonitor.startMonitoring();
  }, 5000); // Start after 5 seconds to allow app to initialize
}

export default healthMonitor;
