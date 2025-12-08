import React from 'react';
import { Wallet, RefreshCw, Eye, Edit, Trash2, Copy, CheckCircle, AlertCircle } from 'lucide-react';
import { Button, Badge, Card, CardContent } from '../ui';
import { useLanguage } from '../../contexts/LanguageContext';

interface TrustWallet {
  id: number;
  wallet_address: string;
  wallet_name: string;
  network: string;
  is_active: boolean;
  created_at: string;
  last_sync_time?: string;
  transaction_count?: number;
}

interface TrustWalletCardProps {
  wallet: TrustWallet;
  onSync: (walletId: number) => void;
  onView: (walletId: number) => void;
  onEdit: (walletId: number) => void;
  onDelete: (walletId: number) => void;
  isSyncing?: boolean;
  isDeleting?: boolean;
}

const TrustWalletCard: React.FC<TrustWalletCardProps> = ({
  wallet,
  onSync,
  onView,
  onEdit,
  onDelete,
  isSyncing = false,
  isDeleting = false
}) => {
  const { t } = useLanguage();
  const [copied, setCopied] = React.useState(false);

  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(wallet.wallet_address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy address:', err);
    }
  };

  const getNetworkColor = (network: string) => {
    switch (network) {
      case 'ETH': return 'bg-blue-100 text-blue-800';
      case 'BSC': return 'bg-yellow-100 text-yellow-800';
      case 'TRC': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
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

  return (
    <div className="border border-gray-200 rounded-lg bg-white hover:shadow-sm transition-shadow duration-200">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <Wallet className="h-5 w-5 text-gray-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {wallet.wallet_name}
              </h4>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getNetworkColor(wallet.network)}`}>
                  {wallet.network}
                </span>
              </div>
            </div>
          </div>
          <div className="flex-shrink-0">
            {wallet.is_active ? (
              <div className="h-2 w-2 bg-green-400 rounded-full" title="Active"></div>
            ) : (
              <div className="h-2 w-2 bg-red-400 rounded-full" title="Inactive"></div>
            )}
          </div>
        </div>

        {/* Address */}
        <div className="mt-4">
          <div className="flex items-center space-x-2 bg-gray-50 rounded-md p-3">
            <span className="text-xs text-gray-600 font-mono truncate flex-1">
              {wallet.wallet_address}
            </span>
            <button
              onClick={copyAddress}
              className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
              title="Copy address"
            >
              {copied ? (
                <CheckCircle className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
          <div>
            <dt className="text-gray-500">Transactions</dt>
            <dd className="text-gray-900 font-medium">{wallet.transaction_count || 0}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Last sync</dt>
            <dd className="text-gray-900 font-medium">{formatLastSync(wallet.last_sync_time)}</dd>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex items-center space-x-2">
          <button
            onClick={() => onSync(wallet.id)}
            disabled={isSyncing}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`h-3 w-3 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync'}
          </button>
          
          <button
            onClick={() => onView(wallet.id)}
            className="inline-flex items-center justify-center p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-md transition-colors"
            title="View details"
          >
            <Eye className="h-3 w-3" />
          </button>
          
          <button
            onClick={() => onEdit(wallet.id)}
            className="inline-flex items-center justify-center p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-md transition-colors"
            title="Edit wallet"
          >
            <Edit className="h-3 w-3" />
          </button>
          
          <button
            onClick={() => onDelete(wallet.id)}
            disabled={isDeleting}
            className={`inline-flex items-center justify-center p-2 rounded-md transition-colors ${
              isDeleting 
                ? 'text-gray-400 cursor-not-allowed' 
                : 'text-red-400 hover:text-red-600 hover:bg-red-50'
            }`}
            title={isDeleting ? "Deleting..." : "Delete wallet"}
          >
            {isDeleting ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <Trash2 className="h-3 w-3" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TrustWalletCard;
