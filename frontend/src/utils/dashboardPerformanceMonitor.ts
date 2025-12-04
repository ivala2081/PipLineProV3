/**
 * Dashboard Performance Monitor
 * Frontend'de dashboard yükleme süresini ve veri tutarlılığını izler
 */

interface PerformanceMetric {
  timestamp: number;
  metric: string;
  duration: number;
  metadata?: Record<string, any>;
}

interface DataSnapshot {
  timestamp: number;
  totalRevenue: string;
  totalTransactions: string;
  activeClients: string;
  exchangeRate: number;
  netCashTL: number;
}

class DashboardPerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private dataSnapshots: DataSnapshot[] = [];
  private loadStartTime: number = 0;
  private apiTimings: Record<string, number> = {};
  private enabled: boolean = true;

  constructor() {
    // LocalStorage'dan önceki metrikleri yükle
    this.loadFromStorage();
  }

  /**
   * Dashboard yükleme başlangıcını işaretle
   */
  startLoad(): void {
    if (!this.enabled) return;
    
    this.loadStartTime = performance.now();
    console.log('%c[PERF] Dashboard load started', 'color: #4CAF50; font-weight: bold');
  }

  /**
   * API çağrısı başlangıcı
   */
  startAPI(apiName: string): void {
    if (!this.enabled) return;
    
    this.apiTimings[`${apiName}_start`] = performance.now();
    console.log(`%c[PERF] ${apiName} API started`, 'color: #2196F3');
  }

  /**
   * API çağrısı bitişi
   */
  endAPI(apiName: string, metadata?: Record<string, any>): void {
    if (!this.enabled) return;
    
    const startKey = `${apiName}_start`;
    if (this.apiTimings[startKey]) {
      const duration = performance.now() - this.apiTimings[startKey];
      
      this.metrics.push({
        timestamp: Date.now(),
        metric: `${apiName}_api`,
        duration,
        metadata
      });

      console.log(
        `%c[PERF] ${apiName} API completed: ${duration.toFixed(2)}ms`,
        duration > 500 ? 'color: #FF5722; font-weight: bold' : 'color: #4CAF50'
      );

      delete this.apiTimings[startKey];
    }
  }

  /**
   * Dashboard yükleme bitişi
   */
  endLoad(dataSnapshot?: Partial<DataSnapshot>): void {
    if (!this.enabled) return;
    
    if (this.loadStartTime) {
      const duration = performance.now() - this.loadStartTime;
      
      this.metrics.push({
        timestamp: Date.now(),
        metric: 'total_load',
        duration,
        metadata: dataSnapshot
      });

      console.log(
        `%c[PERF] Dashboard load completed: ${duration.toFixed(2)}ms`,
        duration > 1000 ? 'color: #FF5722; font-weight: bold' : 'color: #4CAF50; font-weight: bold'
      );

      // Veri snapshot'ı kaydet
      if (dataSnapshot) {
        this.dataSnapshots.push({
          timestamp: Date.now(),
          totalRevenue: dataSnapshot.totalRevenue || '0',
          totalTransactions: dataSnapshot.totalTransactions || '0',
          activeClients: dataSnapshot.activeClients || '0',
          exchangeRate: dataSnapshot.exchangeRate || 0,
          netCashTL: dataSnapshot.netCashTL || 0,
        });
      }

      this.loadStartTime = 0;
      
      // Storage'a kaydet
      this.saveToStorage();
      
      // Analiz yap
      this.analyzeConsistency();
    }
  }

  /**
   * Veri tutarlılığını analiz et
   */
  private analyzeConsistency(): void {
    if (this.dataSnapshots.length < 2) return;

    const lastTwo = this.dataSnapshots.slice(-2);
    const [previous, current] = lastTwo;

    const inconsistencies: string[] = [];

    if (previous.totalRevenue !== current.totalRevenue) {
      inconsistencies.push(`Total Revenue: ${previous.totalRevenue} → ${current.totalRevenue}`);
    }

    if (previous.totalTransactions !== current.totalTransactions) {
      inconsistencies.push(`Total Transactions: ${previous.totalTransactions} → ${current.totalTransactions}`);
    }

    if (previous.activeClients !== current.activeClients) {
      inconsistencies.push(`Active Clients: ${previous.activeClients} → ${current.activeClients}`);
    }

    if (Math.abs(previous.exchangeRate - current.exchangeRate) > 0.01) {
      inconsistencies.push(`Exchange Rate: ${previous.exchangeRate} → ${current.exchangeRate}`);
    }

    if (inconsistencies.length > 0) {
      console.warn(
        '%c[PERF] ⚠️ DATA INCONSISTENCY DETECTED:',
        'color: #FF9800; font-weight: bold; font-size: 14px'
      );
      inconsistencies.forEach(msg => {
        console.warn(`  - ${msg}`);
      });
      
      // İki farklı senaryo tespit edildi!
      this.recordInconsistency(inconsistencies);
    } else {
      console.log(
        '%c[PERF] ✓ Data is consistent',
        'color: #4CAF50; font-weight: bold'
      );
    }
  }

  /**
   * Tutarsızlık kaydet
   */
  private recordInconsistency(inconsistencies: string[]): void {
    const inconsistencyLog = {
      timestamp: Date.now(),
      inconsistencies,
      snapshots: this.dataSnapshots.slice(-2)
    };

    const existingLogs = JSON.parse(
      localStorage.getItem('dashboard_inconsistencies') || '[]'
    );
    
    existingLogs.push(inconsistencyLog);
    
    // Son 50 tutarsızlığı sakla
    if (existingLogs.length > 50) {
      existingLogs.shift();
    }
    
    localStorage.setItem('dashboard_inconsistencies', JSON.stringify(existingLogs));
  }

  /**
   * Performans raporunu konsola yazdır
   */
  printReport(): void {
    if (this.metrics.length === 0) {
      console.log('%c[PERF] No metrics recorded yet', 'color: #999');
      return;
    }

    console.group('%c📊 Dashboard Performance Report', 'color: #2196F3; font-weight: bold; font-size: 16px');

    // API timing'leri
    const apiMetrics = this.metrics.filter(m => m.metric.includes('_api'));
    if (apiMetrics.length > 0) {
      console.group('API Timings (Last 10)');
      apiMetrics.slice(-10).forEach(m => {
        const time = new Date(m.timestamp).toLocaleTimeString();
        console.log(
          `${time} - ${m.metric}: ${m.duration.toFixed(2)}ms`,
          m.metadata || ''
        );
      });
      console.groupEnd();
    }

    // Total load times
    const loadMetrics = this.metrics.filter(m => m.metric === 'total_load');
    if (loadMetrics.length > 0) {
      console.group('Total Load Times (Last 10)');
      
      const durations = loadMetrics.slice(-10).map(m => m.duration);
      const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
      const min = Math.min(...durations);
      const max = Math.max(...durations);

      console.log(`Average: ${avg.toFixed(2)}ms`);
      console.log(`Min: ${min.toFixed(2)}ms`);
      console.log(`Max: ${max.toFixed(2)}ms`);
      
      loadMetrics.slice(-10).forEach(m => {
        const time = new Date(m.timestamp).toLocaleTimeString();
        console.log(`${time}: ${m.duration.toFixed(2)}ms`);
      });
      console.groupEnd();
    }

    // Data snapshots
    if (this.dataSnapshots.length > 0) {
      console.group('Recent Data Snapshots (Last 5)');
      this.dataSnapshots.slice(-5).forEach((snapshot, idx) => {
        const time = new Date(snapshot.timestamp).toLocaleTimeString();
        console.log(`${time}:`, {
          revenue: snapshot.totalRevenue,
          transactions: snapshot.totalTransactions,
          clients: snapshot.activeClients,
          rate: snapshot.exchangeRate
        });
      });
      console.groupEnd();
    }

    // Inconsistency report
    const inconsistencyLogs = JSON.parse(
      localStorage.getItem('dashboard_inconsistencies') || '[]'
    );
    
    if (inconsistencyLogs.length > 0) {
      console.group(`⚠️ Inconsistencies Detected (${inconsistencyLogs.length} total)`);
      inconsistencyLogs.slice(-5).forEach((log: any) => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        console.warn(`${time}:`, log.inconsistencies);
      });
      console.groupEnd();
    }

    console.groupEnd();
  }

  /**
   * Metrikleri localStorage'a kaydet
   */
  private saveToStorage(): void {
    try {
      // Son 100 metriği sakla
      const metricsToSave = this.metrics.slice(-100);
      const snapshotsToSave = this.dataSnapshots.slice(-50);
      
      localStorage.setItem('dashboard_metrics', JSON.stringify(metricsToSave));
      localStorage.setItem('dashboard_snapshots', JSON.stringify(snapshotsToSave));
    } catch (error) {
      console.warn('[PERF] Failed to save metrics to storage:', error);
    }
  }

  /**
   * Metrikleri localStorage'dan yükle
   */
  private loadFromStorage(): void {
    try {
      const savedMetrics = localStorage.getItem('dashboard_metrics');
      const savedSnapshots = localStorage.getItem('dashboard_snapshots');
      
      if (savedMetrics) {
        this.metrics = JSON.parse(savedMetrics);
      }
      
      if (savedSnapshots) {
        this.dataSnapshots = JSON.parse(savedSnapshots);
      }
    } catch (error) {
      console.warn('[PERF] Failed to load metrics from storage:', error);
    }
  }

  /**
   * Tüm metrikleri temizle
   */
  clear(): void {
    this.metrics = [];
    this.dataSnapshots = [];
    localStorage.removeItem('dashboard_metrics');
    localStorage.removeItem('dashboard_snapshots');
    localStorage.removeItem('dashboard_inconsistencies');
    console.log('%c[PERF] Metrics cleared', 'color: #999');
  }

  /**
   * Monitoring'i aç/kapat
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    console.log(`%c[PERF] Monitoring ${enabled ? 'enabled' : 'disabled'}`, 'color: #999');
  }

  /**
   * Export metrics as JSON
   */
  exportMetrics(): string {
    return JSON.stringify({
      metrics: this.metrics,
      dataSnapshots: this.dataSnapshots,
      inconsistencies: JSON.parse(localStorage.getItem('dashboard_inconsistencies') || '[]'),
      exportedAt: new Date().toISOString()
    }, null, 2);
  }
}

// Global singleton instance
export const dashboardPerfMonitor = new DashboardPerformanceMonitor();

// Console helper'ları ekle
if (typeof window !== 'undefined') {
  (window as any).dashboardPerf = {
    report: () => dashboardPerfMonitor.printReport(),
    clear: () => dashboardPerfMonitor.clear(),
    export: () => {
      const data = dashboardPerfMonitor.exportMetrics();
      console.log(data);
      return data;
    },
    enable: () => dashboardPerfMonitor.setEnabled(true),
    disable: () => dashboardPerfMonitor.setEnabled(false)
  };

  console.log(
    '%c💡 Dashboard Performance Monitor Active',
    'color: #2196F3; font-weight: bold; font-size: 14px'
  );
  console.log(
    '%cUse window.dashboardPerf.report() to see performance metrics',
    'color: #666'
  );
}

export default dashboardPerfMonitor;

