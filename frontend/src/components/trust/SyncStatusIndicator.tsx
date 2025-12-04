import React from 'react';
import { 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Zap,
  Activity,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { Badge, Button, Card, CardContent } from '../ui';
import { useLanguage } from '../../contexts/LanguageContext';

interface SyncStatus {
  wallet_id: number;
  wallet_name: string;
  network: string;
  status: 'syncing' | 'success' | 'error' | 'idle';
  last_sync_time?: string;
  last_sync_block?: number;
  current_block?: number;
  transactions_synced?: number;
  error_message?: string;
  progress_percentage?: number;
}

interface SyncStatusIndicatorProps {
  syncStatus: SyncStatus[];
  onSyncAll?: () => void;
  onSyncWallet?: (walletId: number) => void;
  isGlobalSyncing?: boolean;
}

const SyncStatusIndicator: React.FC<SyncStatusIndicatorProps> = ({
  syncStatus,
  onSyncAll,
  onSyncWallet,
  isGlobalSyncing = false
}) => {
  const { t } = useLanguage();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'syncing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'idle':
        return <Clock className="h-4 w-4 text-gray-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'syncing':
        return 'bg-blue-100 text-blue-800';
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'idle':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getNetworkColor = (network: string) => {
    switch (network) {
      case 'ETH':
        return 'bg-blue-100 text-blue-800';
      case 'BSC':
        return 'bg-yellow-100 text-yellow-800';
      case 'TRC':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getOverallStatus = () => {
    const hasError = syncStatus.some(s => s.status === 'error');
    const hasSyncing = syncStatus.some(s => s.status === 'syncing');
    const allSuccess = syncStatus.every(s => s.status === 'success');
    
    if (hasError) return 'error';
    if (hasSyncing) return 'syncing';
    if (allSuccess && syncStatus.length > 0) return 'success';
    return 'idle';
  };

  const overallStatus = getOverallStatus();
  const syncingCount = syncStatus.filter(s => s.status === 'syncing').length;
  const successCount = syncStatus.filter(s => s.status === 'success').length;
  const errorCount = syncStatus.filter(s => s.status === 'error').length;

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Sync Status</h3>
            <Badge className={getStatusColor(overallStatus)}>
              {getStatusIcon(overallStatus)}
              <span className="ml-1 capitalize">{overallStatus}</span>
            </Badge>
          </div>
          {onSyncAll && (
            <Button
              onClick={onSyncAll}
              disabled={isGlobalSyncing}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700"
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${isGlobalSyncing ? 'animate-spin' : ''}`} />
              Sync All
            </Button>
          )}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <RefreshCw className="h-4 w-4 text-blue-500" />
            </div>
            <p className="text-sm font-medium text-gray-600">Syncing</p>
            <p className="text-lg font-bold text-blue-600">{syncingCount}</p>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <CheckCircle className="h-4 w-4 text-green-500" />
            </div>
            <p className="text-sm font-medium text-gray-600">Success</p>
            <p className="text-lg font-bold text-green-600">{successCount}</p>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <AlertCircle className="h-4 w-4 text-red-500" />
            </div>
            <p className="text-sm font-medium text-gray-600">Errors</p>
            <p className="text-lg font-bold text-red-600">{errorCount}</p>
          </div>
        </div>

        {/* Individual Wallet Status */}
        <div className="space-y-3">
          {syncStatus.length === 0 ? (
            <div className="text-center py-4">
              <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600">No wallets configured</p>
            </div>
          ) : (
            syncStatus.map((status) => (
              <div key={status.wallet_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(status.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{status.wallet_name}</p>
                    <div className="flex items-center space-x-2">
                      <Badge className={getNetworkColor(status.network)}>
                        {status.network}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        Last sync: {formatLastSync(status.last_sync_time)}
                      </span>
                    </div>
                    {status.status === 'syncing' && status.progress_percentage !== undefined && (
                      <div className="mt-1">
                        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                          <span>Syncing...</span>
                          <span>{status.progress_percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div 
                            className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${status.progress_percentage}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {status.status === 'error' && status.error_message && (
                      <p className="text-xs text-red-600 mt-1">{status.error_message}</p>
                    )}
                    {status.transactions_synced !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        {status.transactions_synced} transactions synced
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {status.status === 'success' && (
                    <div className="flex items-center text-xs text-green-600">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      Up to date
                    </div>
                  )}
                  {onSyncWallet && (
                    <Button
                      onClick={() => onSyncWallet(status.wallet_id)}
                      disabled={status.status === 'syncing'}
                      variant="outline"
                      size="sm"
                      className="border-gray-300 hover:bg-gray-50"
                    >
                      <RefreshCw className={`h-3 w-3 mr-1 ${status.status === 'syncing' ? 'animate-spin' : ''}`} />
                      Sync
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Global Sync Progress */}
        {isGlobalSyncing && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-900">Global Sync in Progress</span>
              <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
            </div>
            <p className="text-xs text-blue-700">
              Syncing all wallets. This may take a few minutes depending on the number of transactions.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SyncStatusIndicator;
