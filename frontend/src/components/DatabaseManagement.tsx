import { useState, useEffect } from 'react';
import {
  Database,
  RefreshCw,
  Download,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  HardDrive,
  Users,
  Zap,
  Shield,
  Package,
} from 'lucide-react';
import { UnifiedCard, UnifiedButton, UnifiedBadge } from '../design-system';
import { api } from '../utils/apiClient';

interface DatabaseHealth {
  status: string;
  file_info: {
    path: string;
    size_mb: number;
    last_modified: string;
  };
  integrity: string;
  statistics: {
    tables: Record<string, number>;
    total_records: number;
    database_size_mb: number;
    fragmentation_percent: number;
  };
  recommendations: {
    optimize: boolean;
    backup: boolean;
    message: string;
  };
}

interface Backup {
  filename: string;
  size_mb: number;
  created_at: string;
  age_days: number;
  status: string;
}

interface BackupsData {
  backups: Backup[];
  total_count: number;
  total_size_mb: number;
  latest_backup: Backup | null;
}

interface SystemStatus {
  disk_space: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    usage_percent: number;
  };
  disk_status: string;
  database_type: string;
  multi_user: {
    ready: boolean;
    max_recommended_users: number | string;
    current_type: string;
    recommendation: string;
  };
  overall_status: string;
}

export default function DatabaseManagement() {
  const [dbHealth, setDbHealth] = useState<DatabaseHealth | null>(null);
  const [backups, setBackups] = useState<BackupsData | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [optimizing, setOptimizing] = useState(false);

  // Fetch all data
  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const [healthRes, backupsRes, statusRes] = await Promise.all([
        api.get('/api/v1/database-management/health'),
        api.get('/api/v1/database-management/backups'),
        api.get('/api/v1/database-management/system-status'),
      ]);

      const healthData = await api.parseResponse(healthRes);
      const backupsData = await api.parseResponse(backupsRes);
      const statusData = await api.parseResponse(statusRes);

      setDbHealth(healthData.data);
      setBackups(backupsData.data);
      setSystemStatus(statusData.data);
    } catch (error: any) {
      console.error('Error fetching database data:', error);
      console.error('Error:', error.response?.data?.error || 'Failed to fetch database information');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Create backup
  const handleCreateBackup = async () => {
    console.log('🔵 Create Backup clicked!');
    try {
      setCreatingBackup(true);
      console.log('🔵 Calling API...');
      const response = await api.post('/api/v1/database-management/backup');
      console.log('🔵 API Response:', response);
      
      if (response.ok) {
        console.log('🟢 Response OK, parsing...');
        const data = await api.parseResponse(response);
        console.log('🟢 Parsed data:', data);
        console.log('✅ Success:', data.message || 'Backup created successfully!');
        await fetchData(true);
      } else {
        console.log('🔴 Response not OK:', response.status);
        const errorData = await response.json();
        console.log('🔴 Error data:', errorData);
        console.error('Error:', errorData.error || 'Failed to create backup');
      }
    } catch (error: any) {
      console.error('🔴 Error creating backup:', error);
      console.error('Error:', error.message || 'Failed to create backup');
    } finally {
      setCreatingBackup(false);
      console.log('🔵 Create backup finished');
    }
  };

  // Optimize database
  const handleOptimize = async () => {
    if (!confirm('This will optimize the database. A backup will be created automatically. Continue?')) {
      return;
    }

    try {
      setOptimizing(true);
      const response = await api.post('/api/v1/database-management/optimize');
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('✅ Success:', data.message || 'Database optimized successfully!');
        await fetchData(true);
      } else {
        const errorData = await response.json();
        console.error('Error:', errorData.error || 'Failed to optimize database');
      }
    } catch (error: any) {
      console.error('Error optimizing database:', error);
      console.error('Error:', 'Failed to optimize database');
    } finally {
      setOptimizing(false);
    }
  };

  // Download backup
  const handleDownloadBackup = async (filename: string) => {
    try {
      window.open(`/api/v1/database-management/download-backup/${filename}`, '_blank');
      console.log('ℹ️ Downloading:', 'Downloading backup...');
    } catch (error: any) {
      console.error('Error:', 'Failed to download backup');
    }
  };

  // Delete backup
  const handleDeleteBackup = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) {
      return;
    }

    try {
      const response = await api.delete(`/api/v1/database-management/delete-backup/${filename}`);
      
      if (response.ok) {
        const data = await api.parseResponse(response);
        console.log('✅ Success:', data.message || 'Backup deleted successfully');
        await fetchData(true);
      } else {
        const errorData = await response.json();
        console.error('Error:', errorData.error || 'Failed to delete backup');
      }
    } catch (error: any) {
      console.error('Error deleting backup:', error);
      console.error('Error:', 'Failed to delete backup');
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'fresh':
      case 'recent':
        return 'green';
      case 'warning':
      case 'old':
        return 'yellow';
      case 'critical':
      case 'very_old':
        return 'red';
      default:
        return 'gray';
    }
  };

  // Get status badge variant
  const getStatusVariant = (status: string): 'success' | 'warning' | 'destructive' | 'default' => {
    const color = getStatusColor(status);
    if (color === 'green') return 'success';
    if (color === 'yellow') return 'warning';
    if (color === 'red') return 'destructive';
    return 'default';
  };

  // Status badge component using UnifiedBadge
  const StatusBadge = ({ status }: { status: string }) => {
    return (
      <UnifiedBadge variant={getStatusVariant(status)}>
        {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
      </UnifiedBadge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <RefreshCw className="h-8 w-8 animate-spin text-orange-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Refresh Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Database Management</h2>
          <p className="text-sm text-gray-600 mt-1">Monitor health, manage backups, and maintain your database</p>
        </div>
        <UnifiedButton
          onClick={() => fetchData(true)}
          disabled={refreshing}
          variant="outline"
          size="sm"
          loading={refreshing}
          icon={<RefreshCw className="h-4 w-4" />}
        >
          Refresh
        </UnifiedButton>
      </div>

      {/* Database Health Section */}
      <UnifiedCard
        variant="elevated"
        showGlass={true}
        header={{
          title: 'Database Health',
          description: 'Current database status and metrics',
          actions: dbHealth && <StatusBadge status={dbHealth.status} />
        }}
      >
          {dbHealth && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Database Size */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <HardDrive className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">Database Size</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">{dbHealth.statistics.database_size_mb} MB</div>
                <p className="text-xs text-gray-500 mt-1">{dbHealth.statistics.total_records.toLocaleString()} total records</p>
              </div>

              {/* Fragmentation */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">Fragmentation</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">{dbHealth.statistics.fragmentation_percent}%</div>
                <p className="text-xs text-gray-500 mt-1">
                  {dbHealth.statistics.fragmentation_percent < 10 ? 'Optimized' : 'Needs optimization'}
                </p>
              </div>

              {/* Integrity */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-700">Integrity</span>
                </div>
                <div className="text-2xl font-bold text-gray-900 capitalize">{dbHealth.integrity}</div>
                <p className="text-xs text-gray-500 mt-1">No corruption detected</p>
              </div>
            </div>
          )}

          {/* Table Statistics */}
          {dbHealth && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Table Statistics</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(dbHealth.statistics.tables).map(([table, count]) => (
                  <div key={table} className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg">
                    <span className="text-xs text-gray-600">{table}</span>
                    <span className="text-sm font-semibold text-gray-900">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {dbHealth?.recommendations.optimize && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <h5 className="text-sm font-semibold text-yellow-900">Optimization Recommended</h5>
                  <p className="text-sm text-yellow-700 mt-1">
                    Database fragmentation is above 10%. Consider running optimization to improve performance.
                  </p>
                </div>
              </div>
            </div>
          )}
      </UnifiedCard>

      {/* Backup Management Section */}
      <UnifiedCard
        variant="elevated"
        showGlass={true}
        header={{
          title: 'Backup Management',
          description: backups ? `${backups.total_count} backup${backups.total_count !== 1 ? 's' : ''} • ${backups.total_size_mb} MB total` : 'Manage database backups',
          actions: (
            <UnifiedButton
              onClick={handleCreateBackup}
              disabled={creatingBackup}
              size="sm"
              variant="primary"
              loading={creatingBackup}
              icon={<Download className="h-4 w-4" />}
            >
              {creatingBackup ? 'Creating...' : 'Create Backup'}
            </UnifiedButton>
          )
        }}
      >
          {backups && backups.backups.length > 0 ? (
            <div className="space-y-3">
              {backups.backups.map((backup) => (
                <div
                  key={backup.filename}
                  className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <Database className="h-5 w-5 text-gray-600" />
                      <div>
                        <h5 className="text-sm font-medium text-gray-900">{backup.filename}</h5>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-xs text-gray-500">{backup.size_mb} MB</span>
                          <span className="text-xs text-gray-500">•</span>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-gray-400" />
                            <span className="text-xs text-gray-500">
                              {backup.age_days === 0 ? 'Today' : `${backup.age_days} day${backup.age_days !== 1 ? 's' : ''} ago`}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">•</span>
                          <StatusBadge status={backup.status} />
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <UnifiedButton
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadBackup(backup.filename)}
                      icon={<Download className="h-4 w-4" />}
                    >
                      Download
                    </UnifiedButton>
                    {backups.total_count > 1 && (
                      <UnifiedButton
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteBackup(backup.filename)}
                        icon={<Trash2 className="h-4 w-4" />}
                      >
                        Delete
                      </UnifiedButton>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">No backups found</p>
              <UnifiedButton 
                onClick={handleCreateBackup} 
                disabled={creatingBackup}
                variant="primary"
                loading={creatingBackup}
                icon={<Download className="h-4 w-4" />}
              >
                Create First Backup
              </UnifiedButton>
            </div>
          )}
      </UnifiedCard>

      {/* System Status Section */}
      <UnifiedCard
        variant="elevated"
        showGlass={true}
        header={{
          title: 'System Status',
          description: 'Disk space and multi-user readiness'
        }}
      >
          {systemStatus && (
            <div className="space-y-6">
              {/* Disk Space */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h5 className="text-sm font-semibold text-gray-700">Disk Space</h5>
                  <StatusBadge status={systemStatus.disk_status} />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total</span>
                    <span className="font-medium text-gray-900">{systemStatus.disk_space.total_gb} GB</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${
                        systemStatus.disk_space.usage_percent > 90 ? 'bg-red-500' :
                        systemStatus.disk_space.usage_percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${systemStatus.disk_space.usage_percent}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Free</span>
                    <span className="font-medium text-gray-900">{systemStatus.disk_space.free_gb} GB</span>
                  </div>
                </div>
              </div>

              {/* Multi-User Readiness */}
              <div>
                <h5 className="text-sm font-semibold text-gray-700 mb-3">Multi-User Configuration</h5>
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex items-start gap-3">
                    <Users className="h-5 w-5 text-gray-600 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium text-gray-900">{systemStatus.multi_user.current_type}</span>
                        <UnifiedBadge variant={systemStatus.multi_user.ready ? 'success' : 'info'} size="sm">
                          {systemStatus.multi_user.ready ? 'Multi-User Ready' : '1-3 Users'}
                        </UnifiedBadge>
                      </div>
                      <p className="text-sm text-gray-600">{systemStatus.multi_user.recommendation}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
      </UnifiedCard>

      {/* Maintenance Tools Section */}
      <UnifiedCard
        variant="elevated"
        showGlass={true}
        header={{
          title: 'Maintenance Tools',
          description: 'Database optimization and maintenance operations'
        }}
      >
          <div className="space-y-4">
            {/* Optimize Database */}
            <div className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex-1">
                <h5 className="text-sm font-semibold text-gray-900 mb-1">Optimize Database</h5>
                <p className="text-xs text-gray-600">
                  {dbHealth && dbHealth.statistics.fragmentation_percent < 10
                    ? 'Database is well optimized. No optimization needed.'
                    : 'Reduce fragmentation and improve performance.'}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Current fragmentation: {dbHealth?.statistics.fragmentation_percent}%
                </p>
              </div>
              <UnifiedButton
                onClick={handleOptimize}
                disabled={optimizing || (dbHealth ? dbHealth.statistics.fragmentation_percent < 10 : true)}
                size="sm"
                variant={(dbHealth && dbHealth.statistics.fragmentation_percent >= 10) ? 'primary' : 'outline'}
                loading={optimizing}
                icon={<Zap className="h-4 w-4" />}
              >
                {optimizing ? 'Optimizing...' : 'Optimize'}
              </UnifiedButton>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="h-4 w-4 text-blue-600" />
                  <span className="text-xs font-medium text-blue-900">Integrity</span>
                </div>
                <div className="text-lg font-bold text-blue-900">{dbHealth?.integrity.toUpperCase()}</div>
              </div>
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Clock className="h-4 w-4 text-green-600" />
                  <span className="text-xs font-medium text-green-900">Last Modified</span>
                </div>
                <div className="text-xs font-semibold text-green-900">
                  {dbHealth && new Date(dbHealth.file_info.last_modified).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
      </UnifiedCard>

      {/* Info Card */}
      <UnifiedCard variant="outlined" className="border-blue-200 bg-blue-50">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h5 className="text-sm font-semibold text-blue-900 mb-1">Backup Recommendations</h5>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Create backups before major changes</li>
                <li>• Keep at least 7 days of recent backups</li>
                <li>• Download important backups to external storage</li>
                <li>• Run database optimization monthly if fragmentation {'>'} 10%</li>
              </ul>
            </div>
          </div>
      </UnifiedCard>
    </div>
  );
}
