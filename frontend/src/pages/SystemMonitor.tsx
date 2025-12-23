import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Database, 
  HardDrive, 
  Cpu, 
  HardDriveIcon, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Shield,
  BarChart3,
  RefreshCw,
  Settings,
  FileText,
  Table,
  DatabaseIcon,
  Gauge,
  Copy,
  Check
} from 'lucide-react';
import { UnifiedCard, UnifiedButton, UnifiedBadge, UnifiedSection, UnifiedGrid } from '../design-system';
import StandardMetricsCard from '../components/StandardMetricsCard';
import { useLanguage } from '../contexts/LanguageContext';
import PageLayout from '../components/layout/PageLayout';
import { SectionHeader } from '../components/ui/SectionHeader';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  database_connections: number;
  cache_hit_rate: number;
  response_time: number;
  requests_per_second: number;
  error_rate: number;
  uptime: number;
  last_update: string;
  // Extended metrics from API
  system?: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    memory_available_gb?: number;
    memory_used_gb?: number;
    disk_free_gb?: number;
    disk_used_gb?: number;
  };
  cache?: {
    hit_rate: number;
    hits: number;
    misses: number;
    requests_per_second: number;
    avg_response_time: number;
    error_rate: number;
    redis_available: boolean;
    memory_cache_entries: number;
  };
  database_pool?: {
    checked_out: number;
    overflow: number;
    size: number;
  };
  database?: any;
}

interface PerformanceAlert {
  id: string;
  type: 'warning' | 'error' | 'info' | 'success';
  message: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
  recommendations?: string[];
  details?: {
    table?: string;
    row_count?: number;
    suggestions?: string[];
  };
}

interface SystemStatus {
  overall: 'healthy' | 'warning' | 'error' | 'critical';
  database: 'healthy' | 'warning' | 'error';
  cache: 'healthy' | 'warning' | 'error';
  api: 'healthy' | 'warning' | 'error';
  background_tasks: 'healthy' | 'warning' | 'error';
}

interface DatabaseOptimizationResult {
  recommendations: Array<{
    type: 'warning' | 'error' | 'info' | 'success';
    component: string;
    message: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    action: string;
    details: {
      table?: string;
      row_count?: number;
      suggestions?: string[];
      general_tips?: string[];
      error?: string;
    };
  }>;
  total: number;
  timestamp: string;
}

const SystemMonitor: React.FC = () => {
  const { t } = useLanguage();
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [copied, setCopied] = useState(false);
  
  // New state for database optimization
  const [dbOptimization, setDbOptimization] = useState<DatabaseOptimizationResult | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationHistory, setOptimizationHistory] = useState<Array<{
    timestamp: string;
    status: 'success' | 'error' | 'running';
    message: string;
    details?: any;
  }>>([]);
  
  // Raw metrics data for diagnostics
  const [rawMetricsData, setRawMetricsData] = useState<any>(null);
  const [creatingIndex, setCreatingIndex] = useState<string | null>(null);

  useEffect(() => {
    fetchSystemData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchSystemData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
    
    // Return empty cleanup function when autoRefresh is false
    return () => {};
  }, [autoRefresh, refreshInterval]);

  const fetchSystemData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch system metrics
      const metricsResponse = await fetch('/api/v1/performance/status');
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setRawMetricsData(metricsData); // Store raw data for diagnostics
        
        // Map API response to expected frontend structure
        const sanitizedMetrics: SystemMetrics = {
          cpu_usage: typeof metricsData.system?.cpu_percent === 'number' && !isNaN(metricsData.system.cpu_percent) ? metricsData.system.cpu_percent : 0,
          memory_usage: typeof metricsData.system?.memory_percent === 'number' && !isNaN(metricsData.system.memory_percent) ? metricsData.system.memory_percent : 0,
          disk_usage: typeof metricsData.system?.disk_percent === 'number' && !isNaN(metricsData.system.disk_percent) ? metricsData.system.disk_percent : 0,
          database_connections: typeof metricsData.database_pool?.checked_out === 'number' && !isNaN(metricsData.database_pool.checked_out) ? metricsData.database_pool.checked_out : 0,
          cache_hit_rate: typeof metricsData.cache?.hit_rate === 'number' && !isNaN(metricsData.cache.hit_rate) ? metricsData.cache.hit_rate : 
                         (metricsData.cache?.hits && metricsData.cache?.misses) ? 
                         (metricsData.cache.hits / (metricsData.cache.hits + metricsData.cache.misses) * 100) : 0,
          response_time: typeof metricsData.cache?.avg_response_time === 'number' && !isNaN(metricsData.cache.avg_response_time) ? metricsData.cache.avg_response_time : 0,
          requests_per_second: typeof metricsData.cache?.requests_per_second === 'number' && !isNaN(metricsData.cache.requests_per_second) ? metricsData.cache.requests_per_second : 0,
          error_rate: typeof metricsData.cache?.error_rate === 'number' && !isNaN(metricsData.cache.error_rate) ? metricsData.cache.error_rate : 0,
          uptime: typeof metricsData.timestamp === 'number' ? Math.floor((Date.now() / 1000) - metricsData.timestamp) : 0,
          last_update: metricsData.timestamp ? new Date(metricsData.timestamp * 1000).toISOString() : new Date().toISOString(),
          // Store extended metrics
          system: metricsData.system,
          cache: metricsData.cache,
          database_pool: metricsData.database_pool,
          database: metricsData.database
        };
        setMetrics(sanitizedMetrics);
      } else {
        console.warn('Failed to fetch metrics:', metricsResponse.status);
      }
      
      // Fetch system status
      const statusResponse = await fetch('/api/v1/performance/system-status');
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        // Validate and sanitize status data
        const sanitizedStatus = {
          overall: statusData.overall || 'unknown',
          database: statusData.database || 'unknown',
          cache: statusData.cache || 'unknown',
          api: statusData.api || 'unknown',
          background_tasks: statusData.background_tasks || 'unknown'
        };
        setSystemStatus(sanitizedStatus);
      } else {
        console.warn('Failed to fetch system status:', statusResponse.status);
      }
      
      // Fetch performance alerts
      const alertsResponse = await fetch('/api/v1/performance/alerts');
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        // Handle both new format (with alerts array) and legacy format (direct array)
        const alertsArray = Array.isArray(alertsData) ? alertsData : (alertsData.alerts || []);
        setAlerts(alertsArray);
      } else {
        console.warn('Failed to fetch alerts:', alertsResponse.status);
      }
      
    } catch (error) {
      console.error('Error fetching system data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const runDatabaseOptimization = async () => {
    try {
      setIsOptimizing(true);
      
      // Add to history
      const historyEntry = {
        timestamp: new Date().toISOString(),
        status: 'running' as const,
        message: 'Database optimization in progress...'
      };
      setOptimizationHistory(prev => [historyEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
      
      const response = await fetch('/api/v1/performance/database-optimization');
      if (response.ok) {
        const data = await response.json();
        setDbOptimization(data);
        
        // Update history with success
        setOptimizationHistory(prev => [{
          timestamp: new Date().toISOString(),
          status: 'success',
          message: `Optimization completed successfully! Found ${data.total} recommendations.`,
          details: data
        }, ...prev.slice(0, 9)]);
        
        // Add database optimization alerts to the alerts list
        const dbAlerts = data.recommendations.map((rec: any) => ({
          id: `db_opt_${Date.now()}_${Math.random()}`,
          type: rec.type,
          message: rec.message,
          timestamp: new Date().toISOString(),
          severity: rec.priority,
          resolved: false,
          recommendations: rec.details?.general_tips || [],
          details: rec.details
        }));
        setAlerts(prev => [...prev, ...dbAlerts]);
        
      } else {
        throw new Error('Failed to run optimization');
      }
    } catch (error) {
      console.error('Error running database optimization:', error);
      
      // Update history with error
      setOptimizationHistory(prev => [{
        timestamp: new Date().toISOString(),
        status: 'error',
        message: 'Database optimization failed. Please check the logs.',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }, ...prev.slice(0, 9)]);
    } finally {
      setIsOptimizing(false);
    }
  };

  const getStatusColor = (status: string) => {
    // Legacy helper kept for compatibility in a few places; prefer UnifiedBadge variants.
    return 'text-gray-700 bg-gray-100';
  };

  const getStatusIcon = (status: string) => {
    if (!status) return <Clock className="w-5 h-5 text-gray-600" />;
    
    switch (status.toLowerCase()) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-gray-700" />;
      case 'warning': return <AlertTriangle className="w-5 h-5 text-gray-700" />;
      case 'error': return <AlertTriangle className="w-5 h-5 text-gray-700" />;
      case 'critical': return <AlertTriangle className="w-5 h-5 text-gray-900" />;
      default: return <Clock className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusBadgeVariant = (status?: string) => {
    switch ((status || '').toLowerCase()) {
      case 'healthy':
        return 'success' as const;
      case 'warning':
        return 'warning' as const;
      case 'error':
      case 'critical':
        return 'destructive' as const;
      default:
        return 'secondary' as const;
    }
  };

  const getSeverityColor = (severity: string) => {
    if (!severity) return 'border-l-gray-500 bg-gray-50';
    
    switch (severity.toLowerCase()) {
      case 'low': return 'border-l-gray-500 bg-gray-50';
      case 'medium': return 'border-l-gray-600 bg-gray-50';
      case 'high': return 'border-l-gray-700 bg-gray-50';
      case 'critical': return 'border-l-gray-900 bg-gray-50';
      default: return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getProgressBarColor = (value: number) => {
    // Keep status signaling, but align with PipLinePro neutral palette (no vivid colors)
    if (value > 80) return 'bg-gray-900';
    if (value > 60) return 'bg-gray-700';
    return 'bg-gray-500';
  };

  const getProgressBarColorFromHitRate = (hitRate: number) => {
    if (hitRate > 70) return 'bg-gray-700';
    if (hitRate > 50) return 'bg-gray-600';
    return 'bg-gray-500';
  };

  const copyDiagnostics = async () => {
    try {
      const diagnostics = {
        timestamp: new Date().toISOString(),
        system_status: systemStatus,
        metrics: rawMetricsData || metrics,
        alerts: alerts,
        database_optimization: dbOptimization,
        optimization_history: optimizationHistory
      };
      
      const diagnosticsText = JSON.stringify(diagnostics, null, 2);
      await navigator.clipboard.writeText(diagnosticsText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy diagnostics:', error);
    }
  };

  const createIndex = async (rec: any) => {
    if (!rec.details?.table || !rec.details?.index || !rec.details?.columns) {
      console.error('Missing index information');
      return;
    }

    try {
      setCreatingIndex(rec.details.index);
      
      const response = await fetch('/api/v1/performance/database-optimization/create-index', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          table: rec.details.table,
          index: rec.details.index,
          columns: rec.details.columns
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Refresh optimization results
        await runDatabaseOptimization();
        // Show success message (you could add a toast notification here)
        alert(t('system_monitor.index_created_success', { index: rec.details.index }));
      } else {
        throw new Error(data.message || t('system_monitor.failed_to_create_index'));
      }
    } catch (error) {
      console.error('Error creating index:', error);
      alert(`${t('system_monitor.failed_to_create_index')}: ${error instanceof Error ? error.message : t('system_monitor.unknown')}`);
    } finally {
      setCreatingIndex(null);
    }
  };

  return (
    <>
      <PageLayout theme="plain" minHeightScreen={false}>
      <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <SectionHeader
          title={t('navigation.system_monitor', 'System Monitor')}
          description={t('navigation.realtime_system_monitoring', 'Real-time system performance and health monitoring')}
          icon={Activity}
          actions={
            <div className="flex items-center gap-3">
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={copyDiagnostics}
                icon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                iconPosition="left"
              >
                {copied ? t('common.copied', 'Copied') : t('system_monitor.copy_diagnostics', 'Copy Diagnostics')}
              </UnifiedButton>

              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={fetchSystemData}
                disabled={isLoading}
                icon={<RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />}
                iconPosition="left"
              >
                {isLoading ? t('common.refreshing', 'Refreshing') : t('common.refresh', 'Refresh')}
              </UnifiedButton>

              <UnifiedButton
                variant="primary"
                size="sm"
                onClick={runDatabaseOptimization}
                disabled={isOptimizing}
                icon={<Settings className="w-4 h-4" />}
                iconPosition="left"
              >
                {isOptimizing ? t('system_monitor.optimizing', 'Optimizing') : t('system_monitor.run_db_optimization', 'Run DB Optimization')}
              </UnifiedButton>

              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="rounded border-gray-300 text-gray-700 focus:ring-gray-500"
                  />
                  {t('system_monitor.auto_refresh', 'Auto-refresh')}
                </label>

                {autoRefresh && (
                  <select
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(Number(e.target.value))}
                    className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-gray-500 bg-white"
                  >
                    <option value={15}>{t('system_monitor.refresh_interval_15s', '15s')}</option>
                    <option value={30}>{t('system_monitor.refresh_interval_30s', '30s')}</option>
                    <option value={60}>{t('system_monitor.refresh_interval_1m', '1m')}</option>
                    <option value={300}>{t('system_monitor.refresh_interval_5m', '5m')}</option>
                  </select>
                )}
              </div>
            </div>
          }
        />
          
          <div className="flex items-center justify-between text-sm">
            <div className="text-gray-500">
              {t('system_monitor.last_updated', 'Last updated')}: {metrics?.last_update || t('system_monitor.never', 'Never')}
            </div>
            
            {/* Database Optimization Status */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-gray-400" />
                <span className="text-gray-500">DB Status:</span>
                {!dbOptimization ? (
                  <UnifiedBadge variant="secondary" size="sm">{t('system_monitor.not_analyzed', 'Not Analyzed')}</UnifiedBadge>
                ) : isOptimizing ? (
                  <UnifiedBadge variant="warning" size="sm">{t('system_monitor.optimizing', 'Optimizing')}</UnifiedBadge>
                ) : (
                  <UnifiedBadge variant="success" size="sm">
                    {t('system_monitor.optimized', 'Optimized')} ({dbOptimization.total})
                  </UnifiedBadge>
                )}
              </div>
              
              {dbOptimization && (
                <div className="text-xs text-gray-400">
                  {t('system_monitor.last_run', 'Last run')}: {new Date(dbOptimization.timestamp).toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-600"></div>
            <span className="ml-3 text-gray-600">{t('system_monitor.loading_system_data', 'Loading system data...')}</span>
          </div>
        )}

        {/* Error State */}
        {!isLoading && !metrics && !systemStatus && (
          <UnifiedCard variant="elevated" className="p-6 text-center">
            <div className="text-red-600 mb-3">
              <AlertTriangle className="w-12 h-12 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to load system data</h3>
            <p className="text-gray-600 mb-4">Unable to fetch system metrics and status information.</p>
            <UnifiedButton variant="outline" size="sm" onClick={fetchSystemData}>
              Retry
            </UnifiedButton>
          </UnifiedCard>
        )}

        {/* System Status Overview */}
        {!isLoading && systemStatus && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
            <UnifiedCard variant="flat" padding="sm" className="border border-gray-200">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-500">Overall</p>
                  <div className="mt-1">
                    <UnifiedBadge variant={getStatusBadgeVariant(systemStatus.overall)} size="sm">
                      {(systemStatus.overall || 'unknown').charAt(0).toUpperCase() + (systemStatus.overall || 'unknown').slice(1)}
                    </UnifiedBadge>
                  </div>
                </div>
                <div className="shrink-0">{getStatusIcon(systemStatus.overall)}</div>
              </div>
            </UnifiedCard>

            <UnifiedCard variant="flat" padding="sm" className="border border-gray-200">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-500">Database</p>
                  <div className="mt-1">
                    <UnifiedBadge variant={getStatusBadgeVariant(systemStatus.database)} size="sm">
                      {(systemStatus.database || 'unknown').charAt(0).toUpperCase() + (systemStatus.database || 'unknown').slice(1)}
                    </UnifiedBadge>
                  </div>
                </div>
                <Database className="w-5 h-5 text-gray-600 shrink-0" />
              </div>
            </UnifiedCard>

            <UnifiedCard variant="flat" padding="sm" className="border border-gray-200">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-500">DB Optimization</p>
                  <div className="mt-1">
                    {!dbOptimization ? (
                      <UnifiedBadge variant="secondary" size="sm">Not Analyzed</UnifiedBadge>
                    ) : isOptimizing ? (
                      <UnifiedBadge variant="warning" size="sm">Running</UnifiedBadge>
                    ) : (
                      <UnifiedBadge variant="success" size="sm">{dbOptimization.total}</UnifiedBadge>
                    )}
                  </div>
                </div>
                <Settings className="w-5 h-5 text-gray-600 shrink-0" />
              </div>
            </UnifiedCard>

            <UnifiedCard variant="flat" padding="sm" className="border border-gray-200">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-500">Cache</p>
                  <div className="mt-1">
                    <UnifiedBadge variant={getStatusBadgeVariant(systemStatus.cache)} size="sm">
                      {(systemStatus.cache || 'unknown').charAt(0).toUpperCase() + (systemStatus.cache || 'unknown').slice(1)}
                    </UnifiedBadge>
                  </div>
                </div>
                <HardDrive className="w-5 h-5 text-gray-600 shrink-0" />
              </div>
            </UnifiedCard>

            <UnifiedCard variant="flat" padding="sm" className="border border-gray-200">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-500">Background</p>
                  <div className="mt-1">
                    <UnifiedBadge variant={getStatusBadgeVariant(systemStatus.background_tasks)} size="sm">
                      {(systemStatus.background_tasks || 'unknown').charAt(0).toUpperCase() + (systemStatus.background_tasks || 'unknown').slice(1)}
                    </UnifiedBadge>
                  </div>
                </div>
                <BarChart3 className="w-5 h-5 text-gray-600 shrink-0" />
              </div>
            </UnifiedCard>
          </div>
        )}

        {/* API Health Tracker */}
        {!isLoading && systemStatus && (
          <UnifiedCard variant="elevated" className="p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Server className="w-5 h-5 text-gray-600" />
                API Health
              </h3>
              <UnifiedBadge variant={getStatusBadgeVariant(systemStatus.api)} size="sm">
                {(systemStatus.api || 'unknown').charAt(0).toUpperCase() + (systemStatus.api || 'unknown').slice(1)}
              </UnifiedBadge>
            </div>
            <p className="text-sm text-gray-600">
              Current API health status from the system monitor endpoint.
            </p>
          </UnifiedCard>
        )}

        {/* Performance Metrics */}
        {!isLoading && metrics && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* System Resources */}
            <UnifiedCard variant="elevated" className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-gray-600" />
                System Resources
              </h3>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">CPU Usage</span>
                    <span className="font-medium">{(metrics.cpu_usage ?? 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getProgressBarColor(metrics.cpu_usage ?? 0)}`}
                      style={{ width: `${Math.min(metrics.cpu_usage ?? 0, 100)}%` }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Memory Usage</span>
                    <span className="font-medium">{(metrics.memory_usage ?? 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getProgressBarColor(metrics.memory_usage ?? 0)}`}
                      style={{ width: `${Math.min(metrics.memory_usage ?? 0, 100)}%` }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Disk Usage</span>
                    <span className="font-medium">{(metrics.disk_usage ?? 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getProgressBarColor(metrics.disk_usage ?? 0)}`}
                      style={{ width: `${Math.min(metrics.disk_usage ?? 0, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </UnifiedCard>

            {/* Application Performance */}
            <UnifiedCard variant="elevated" className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-gray-600" />
                Application Performance
              </h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-600">{(metrics.response_time ?? 0).toFixed(2)}ms</p>
                    <p className="text-sm text-gray-600">Response Time</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900">{(metrics.requests_per_second ?? 0).toFixed(1)}</p>
                    <p className="text-sm text-gray-600">Requests/sec</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900">{metrics.database_connections ?? 0}</p>
                    <p className="text-sm text-gray-600">DB Connections</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900">{(metrics.cache_hit_rate ?? 0).toFixed(1)}%</p>
                    <p className="text-sm text-gray-600">Cache Hit Rate</p>
                  </div>
                </div>
                
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">{(metrics.error_rate ?? 0).toFixed(2)}%</p>
                  <p className="text-sm text-gray-600">Error Rate</p>
                </div>
              </div>
            </UnifiedCard>
          </div>
        )}

        {/* Redis & Database Pool Metrics */}
        {!isLoading && metrics && (metrics.cache || metrics.database_pool) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Redis Cache Metrics */}
            {metrics.cache && (
              <UnifiedCard variant="elevated" className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-gray-600" />
                  Redis Cache
                  <UnifiedBadge variant={metrics.cache.redis_available ? 'success' : 'warning'} size="sm">
                    {metrics.cache.redis_available ? 'Available' : 'Memory Cache'}
                  </UnifiedBadge>
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Hit Rate</span>
                      <span className="font-medium">{(metrics.cache.hit_rate ?? 0).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getProgressBarColorFromHitRate(metrics.cache.hit_rate ?? 0)}`}
                        style={{ width: `${Math.min(metrics.cache.hit_rate ?? 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{metrics.cache.hits ?? 0}</p>
                      <p className="text-sm text-gray-600">Cache Hits</p>
                    </div>
                    
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{metrics.cache.misses ?? 0}</p>
                      <p className="text-sm text-gray-600">Cache Misses</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{(metrics.cache.avg_response_time ?? 0).toFixed(2)}ms</p>
                      <p className="text-sm text-gray-600">Avg Response</p>
                    </div>
                    
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{metrics.cache.memory_cache_entries ?? 0}</p>
                      <p className="text-sm text-gray-600">Memory Entries</p>
                    </div>
                  </div>
                  
                  {!metrics.cache.redis_available && (
                    <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                      <p className="text-sm text-gray-700">
                        <AlertTriangle className="w-4 h-4 inline mr-2" />
                        {t('system_monitor.redis_unavailable_message', 'Redis is not available. Using in-memory cache (not persistent across restarts).')}
                      </p>
                    </div>
                  )}
                </div>
              </UnifiedCard>
            )}
            
            {/* Database Connection Pool */}
            {metrics.database_pool && (
              <UnifiedCard variant="elevated" className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Database className="w-5 h-5 text-gray-600" />
                  Database Connection Pool
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Pool Usage</span>
                      <span className="font-medium">
                        {metrics.database_pool.checked_out ?? 0} / {metrics.database_pool.size ?? 0}
                        {metrics.database_pool.size > 0 && ` (${((metrics.database_pool.checked_out / metrics.database_pool.size) * 100).toFixed(1)}%)`}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getProgressBarColor(
                          metrics.database_pool.size > 0
                            ? ((metrics.database_pool.checked_out / metrics.database_pool.size) * 100)
                            : 0
                        )}`}
                        style={{ 
                          width: `${metrics.database_pool.size > 0 
                            ? Math.min((metrics.database_pool.checked_out / metrics.database_pool.size) * 100, 100) 
                            : 0}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{metrics.database_pool.checked_out ?? 0}</p>
                      <p className="text-sm text-gray-600">Active Connections</p>
                    </div>
                    
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">{metrics.database_pool.size ?? 0}</p>
                      <p className="text-sm text-gray-600">Pool Size</p>
                    </div>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900">{metrics.database_pool.overflow ?? 0}</p>
                    <p className="text-sm text-gray-600">Overflow Connections</p>
                    {metrics.database_pool.overflow > 0 && (
                      <p className="text-xs text-gray-600 mt-1">
                        <AlertTriangle className="w-3 h-3 inline mr-1" />
                        Pool exhausted, using overflow connections
                      </p>
                    )}
                  </div>
                  
                  {metrics.database_pool.size > 0 && ((metrics.database_pool.checked_out / metrics.database_pool.size) * 100) > 80 && (
                    <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                      <p className="text-sm text-gray-700">
                        <AlertTriangle className="w-4 h-4 inline mr-2" />
                        High pool usage detected. Consider increasing pool size or optimizing connection usage.
                      </p>
                    </div>
                  )}
                </div>
              </UnifiedCard>
            )}
          </div>
        )}

        {/* Database Optimization Results */}
        {!isLoading && (
          <UnifiedCard variant="elevated" className="p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Database className="w-5 h-5 text-gray-600" />
                Database Optimization
              </h3>
              <div className="flex items-center gap-2">
                <UnifiedButton
                  variant="primary"
                  size="sm"
                  onClick={runDatabaseOptimization}
                  disabled={isOptimizing}
                  icon={<Settings className="w-4 h-4" />}
                  iconPosition="left"
                >
                  {isOptimizing ? 'Optimizing' : 'Run Optimization'}
                </UnifiedButton>
              </div>
            </div>
            
            {!dbOptimization ? (
              <div className="text-center py-8 text-gray-500">
                <Database className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p className="text-lg font-medium mb-2">No optimization data yet</p>
                <p className="text-sm">Click "Run Optimization" to analyze your database performance</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-5 h-5 text-gray-600" />
                    <span className="font-medium text-gray-800">Optimization Analysis Complete</span>
                  </div>
                  <p className="text-sm text-gray-700">
                    Found {dbOptimization.total} optimization opportunities. Last run: {new Date(dbOptimization.timestamp).toLocaleString()}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {dbOptimization.recommendations.map((rec, index) => (
                    <div key={index} className="border border-gray-200 bg-gray-50 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-2 h-2 rounded-full mt-2 bg-gray-500"></div>
                        <div className="flex-1">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h4 className="font-medium text-gray-900">{rec.message}</h4>
                            {rec.details?.index && rec.details?.columns && (
                              <UnifiedButton
                                variant="outline"
                                size="sm"
                                onClick={() => createIndex(rec)}
                                disabled={creatingIndex === rec.details.index}
                                icon={creatingIndex === rec.details.index ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Database className="w-3 h-3" />}
                                iconPosition="left"
                              >
                                {creatingIndex === rec.details.index ? t('system_monitor.creating') : t('system_monitor.create_index')}
                              </UnifiedButton>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{rec.action}</p>
                          
                          {rec.details?.table && (
                            <div className="text-xs text-gray-500 mb-2">
                              <span className="font-medium">{t('system_monitor.table')}</span> {rec.details.table}
                              {rec.details.row_count && (
                                <span className="ml-2">({rec.details.row_count.toLocaleString()} {t('system_monitor.rows')})</span>
                              )}
                            </div>
                          )}
                          
                          {rec.details?.suggestions && rec.details.suggestions.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-gray-600 mb-1">{t('system_monitor.suggestions')}</p>
                              <ul className="text-xs text-gray-600 space-y-1">
                                {rec.details.suggestions.map((suggestion, idx) => (
                                  <li key={idx} className="flex items-start gap-2">
                                    <span className="text-gray-500 mt-1">•</span>
                                    <code className="text-xs bg-gray-100 px-1 rounded">{suggestion}</code>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {rec.details?.general_tips && rec.details.general_tips.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-gray-600 mb-1">{t('system_monitor.best_practices')}</p>
                              <ul className="text-xs text-gray-600 space-y-1">
                                {rec.details.general_tips.map((tip, idx) => (
                                  <li key={idx} className="flex items-start gap-2">
                                    <span className="text-gray-500 mt-1">•</span>
                                    {tip}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </UnifiedCard>
        )}

        {/* Performance Alerts */}
        {!isLoading && (
          <UnifiedCard variant="elevated" className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-gray-600" />
              {t('system_monitor.performance_alerts')}
            </h3>
            
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p>{t('system_monitor.no_active_alerts')}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-lg border-l-4 ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <UnifiedBadge variant="secondary" size="sm">
                            {(alert.severity || 'low').toUpperCase()}
                          </UnifiedBadge>
                          <span className="text-sm text-gray-500">{alert.timestamp || 'Unknown'}</span>
                        </div>
                        <p className="text-gray-900 font-medium mb-2">{alert.message || 'No message'}</p>
                        
                        {/* Display recommendations if available */}
                        {alert.recommendations && Array.isArray(alert.recommendations) && (
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-2">{t('system_monitor.recommendations')}</p>
                            <ul className="space-y-1">
                              {alert.recommendations.map((rec, index) => (
                                <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                                  <span className="text-gray-500 mt-1">•</span>
                                  <span>{rec}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {/* Display additional details if available */}
                        {alert.details && (
                          <div className="mt-3 p-3 bg-gray-50 rounded-md">
                            <p className="text-sm font-medium text-gray-700 mb-2">{t('system_monitor.details')}</p>
                            {alert.details.table && (
                              <p className="text-sm text-gray-600">{t('system_monitor.table')} <span className="font-medium">{alert.details.table}</span></p>
                            )}
                            {alert.details.row_count && (
                              <p className="text-sm text-gray-600">{t('system_monitor.rows')}: <span className="font-medium">{alert.details.row_count.toLocaleString()}</span></p>
                            )}
                            {alert.details.suggestions && Array.isArray(alert.details.suggestions) && (
                              <div className="mt-2">
                                <p className="text-sm font-medium text-gray-700 mb-1">{t('system_monitor.specific_actions')}</p>
                                <ul className="space-y-1">
                                  {alert.details.suggestions.map((suggestion, index) => (
                                    <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                                      <span className="text-gray-500 mt-1">→</span>
                                      <span>{suggestion}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <button
                        onClick={() => {
                          setAlerts(alerts.filter(a => a.id !== alert.id));
                        }}
                        className="text-gray-400 hover:text-gray-600 ml-4"
                        title={t('system_monitor.dismiss_alert')}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </UnifiedCard>
        )}

        {/* Database Optimization History */}
        {!isLoading && (
          <UnifiedCard variant="elevated" className="p-6 mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5 text-gray-600" />
              {t('system_monitor.database_optimization_history')}
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('system_monitor.timestamp')}
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('system_monitor.status')}
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('system_monitor.message')}
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {t('system_monitor.details')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {optimizationHistory.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(item.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <UnifiedBadge variant="secondary" size="sm">
                          {item.status.toUpperCase()}
                        </UnifiedBadge>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {item.message}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {item.details && (
                          <button
                            onClick={() => {
                              setOptimizationHistory(optimizationHistory.map((h, i) => 
                                i === index ? { ...h, details: null } : h
                              ));
                            }}
                            className="text-gray-600 hover:underline text-xs"
                          >
                            {t('system_monitor.view_details')}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </UnifiedCard>
        )}

        {/* System Information */}
        {!isLoading && (
          <UnifiedCard variant="elevated" className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-gray-600" />
              {t('system_monitor.system_information')}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">{t('system_monitor.uptime')}</p>
                <p className="font-medium">{metrics?.uptime ? `${Math.floor(metrics.uptime / 3600)}h ${Math.floor((metrics.uptime % 3600) / 60)}m` : t('system_monitor.unknown')}</p>
              </div>
              
              <div>
                <p className="text-gray-600">{t('system_monitor.last_update')}</p>
                <p className="font-medium">{metrics?.last_update || t('system_monitor.never')}</p>
              </div>
              
              <div>
                <p className="text-gray-600">{t('system_monitor.environment')}</p>
                <p className="font-medium">Production</p>
              </div>
              
              <div>
                <p className="text-gray-600">{t('system_monitor.version')}</p>
                <p className="font-medium">PipLinePro v2.0</p>
              </div>
            </div>
          </UnifiedCard>
        )}
      </div>
      </PageLayout>
    </>
  );
};

export default SystemMonitor;