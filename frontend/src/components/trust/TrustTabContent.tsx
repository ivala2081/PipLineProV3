import React, { useState, useEffect, useMemo } from 'react';
import { Plus, RefreshCw, Wallet, AlertCircle, Search, Eye, Trash2, X, ArrowUpDown, ArrowUp, ArrowDown, Clock, CheckCircle, XCircle, TrendingUp, TrendingDown, RotateCcw, Download, Filter, List, Grid, Layers, ExternalLink, Copy, Check, DollarSign, Activity, ChevronDown, Edit, Save, History, MoreVertical, Info } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { api } from '../../utils/apiClient';
import AddWalletModal from './AddWalletModal';
import * as XLSX from 'xlsx';
import { UnifiedCard, UnifiedButton, UnifiedBadge } from '../../design-system';

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

interface TrustSummary {
  overall: {
    total_transactions: number;
    total_amount_try: number;
    total_gas_fee_try: number;
    active_wallets: number;
    unique_tokens: number;
  };
  by_network: Array<{
    network: string;
    transaction_count: number;
    total_amount_try: number;
  }>;
  by_token?: Array<{
    token_symbol: string;
    transaction_count: number;
    total_amount: number;
    total_amount_try: number;
  }>;
}

interface TrustTransaction {
  id: number;
  wallet_id: number;
  transaction_hash: string;
  block_number: number;
  block_timestamp: string;
  from_address: string;
  to_address: string;
  token_symbol: string;
  token_name?: string;
  token_address?: string;
  token_amount: number;
  token_decimals: number;
  transaction_type: 'IN' | 'OUT' | 'INTERNAL';
  gas_fee: number;
  gas_fee_token: string;
  status: 'CONFIRMED' | 'PENDING' | 'FAILED';
  confirmations: number;
  network: string;
  notes?: string;
}

const TrustTabContent: React.FC = () => {
  const { t } = useLanguage();
  
  // State management
  const [wallets, setWallets] = useState<TrustWallet[]>([]);
  const [summary, setSummary] = useState<TrustSummary | null>(null);
  const [transactions, setTransactions] = useState<TrustTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [walletsLoading, setWalletsLoading] = useState(false);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [syncingWallets, setSyncingWallets] = useState<Set<number>>(new Set());
  const [deletingWallets, setDeletingWallets] = useState<Set<number>>(new Set());
  const [showAddModal, setShowAddModal] = useState(false);
  const [showWalletModal, setShowWalletModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedWallet, setSelectedWallet] = useState<TrustWallet | null>(null);
  const [editingWallet, setEditingWallet] = useState<TrustWallet | null>(null);
  const [deletingWalletId, setDeletingWalletId] = useState<number | null>(null);
  const [deleteSecurityCode, setDeleteSecurityCode] = useState('');
  const [walletTransactions, setWalletTransactions] = useState<TrustTransaction[]>([]);
  const [walletTransactionsLoading, setWalletTransactionsLoading] = useState(false);
  const [walletBalances, setWalletBalances] = useState<{[key: number]: any}>({});
  const [balancesLoading, setBalancesLoading] = useState<{[key: number]: boolean}>({});
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [networkFilter, setNetworkFilter] = useState('all');
  const [copiedWalletId, setCopiedWalletId] = useState<number | null>(null);

  // Wallet modal state
  const [modalSearchTerm, setModalSearchTerm] = useState('');
  const [modalTypeFilter, setModalTypeFilter] = useState<string>('all');
  const [modalTokenFilter, setModalTokenFilter] = useState<string>('all');
  const [modalStatusFilter, setModalStatusFilter] = useState<string>('all');
  const [modalSortBy, setModalSortBy] = useState<'date' | 'amount' | 'gas'>('date');
  const [modalSortOrder, setModalSortOrder] = useState<'asc' | 'desc'>('desc');
  const [modalViewMode, setModalViewMode] = useState<'detailed' | 'compact'>('detailed');
  const [modalGroupByDay, setModalGroupByDay] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [transactionsPerPage, setTransactionsPerPage] = useState(50);
  
  // Historical balances state
  const [modalView, setModalView] = useState<'transactions' | 'historical'>('transactions');
  const [historicalBalances, setHistoricalBalances] = useState<any[]>([]);
  const [historicalBalancesLoading, setHistoricalBalancesLoading] = useState(false);
  const [historicalStartDate, setHistoricalStartDate] = useState<string>('');
  const [historicalEndDate, setHistoricalEndDate] = useState<string>('');

  // Reset copied state after a delay
  useEffect(() => {
    if (copiedWalletId === null) return;

    const timeout = window.setTimeout(() => setCopiedWalletId(null), 2000);
    return () => window.clearTimeout(timeout);
  }, [copiedWalletId]);

  // Load initial data
  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        loadWallets(),
        loadSummary(),
        loadTransactions()
      ]);
    } catch (err) {
      console.error('Error loading Trust Wallet data:', err);
      setError('Failed to load Trust Wallet data');
    } finally {
      setLoading(false);
    }
  };

  const loadWallets = async () => {
    try {
      setWalletsLoading(true);
      const response = await api.get('/trust-wallet/wallets');
      const responseData = await api.parseResponse<{success: boolean; wallets: TrustWallet[]}>(response);
      if (responseData.success) {
        setWallets(responseData.wallets || []);
        // Load balances for all wallets
        responseData.wallets?.forEach(wallet => {
          loadWalletBalance(wallet.id);
        });
      }
    } catch (err) {
      console.error('Error loading wallets:', err);
    } finally {
      setWalletsLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const response = await api.get('/trust-wallet/summary');
      const responseData = await api.parseResponse<{success: boolean; overall: any; by_network: any[]; by_token?: any[]}>(response);
      if (responseData.success) {
        // Backend unpacks summary with **summary, so we need to restructure it
        setSummary({
          overall: responseData.overall,
          by_network: responseData.by_network,
          by_token: responseData.by_token
        });
      }
    } catch (err) {
      console.error('Error loading summary:', err);
    }
  };

  const loadTransactions = async () => {
    try {
      setTransactionsLoading(true);
      const response = await api.get('/trust-wallet/transactions?per_page=50');
      const responseData = await api.parseResponse<{success: boolean; transactions: TrustTransaction[]}>(response);
      if (responseData.success) {
        setTransactions(responseData.transactions || []);
      }
    } catch (err) {
      console.error('Error loading transactions:', err);
    } finally {
      setTransactionsLoading(false);
    }
  };

  const handleSyncWallet = async (walletId: number) => {
    setSyncingWallets(prev => new Set(prev).add(walletId));
    
    try {
      // Always use force_full_sync to ensure we get ALL transactions
      const response = await api.post(`/trust-wallet/wallets/${walletId}/sync`, {
        force_full_sync: true
      });
      
      const responseData = await api.parseResponse<{success: boolean; error?: string; details?: string; sync_result?: any}>(response);
      
      if (responseData.success) {
        // Refresh data after sync
        await Promise.all([loadWallets(), loadSummary(), loadTransactions()]);
        // If wallet modal is open, reload its transactions too
        if (selectedWallet && selectedWallet.id === walletId) {
          await loadWalletTransactions(walletId);
        }
      } else {
        const errorMsg = responseData.error || 'Failed to sync wallet';
        const details = responseData.details || '';
        console.error('Sync error:', errorMsg, details);
        setError(`${errorMsg}${details ? `: ${details}` : ''}`);
      }
    } catch (err: any) {
      console.error('Error syncing wallet:', err);
      const errorMsg = err?.message || err?.response?.error || 'Failed to sync wallet';
      const details = err?.details || err?.response?.details || '';
      const fullError = `${errorMsg}${details ? `: ${details}` : ''}`;
      console.error('Full sync error:', fullError);
      setError(fullError);
    } finally {
      setSyncingWallets(prev => {
        const newSet = new Set(prev);
        newSet.delete(walletId);
        return newSet;
      });
    }
  };

  const handleViewWallet = async (walletId: number) => {
    const wallet = wallets.find(w => w.id === walletId);
    if (!wallet) return;
    
    setSelectedWallet(wallet);
    setShowWalletModal(true);
    setModalView('transactions');
    await loadWalletTransactions(walletId);
  };
  
  const loadHistoricalBalances = async (walletId: number) => {
    try {
      setHistoricalBalancesLoading(true);
      const params = new URLSearchParams();
      if (historicalStartDate) params.append('start_date', historicalStartDate);
      if (historicalEndDate) params.append('end_date', historicalEndDate);
      
      const response = await api.get(`/trust-wallet/wallets/${walletId}/historical-balances?${params.toString()}`);
      const responseData = await api.parseResponse<{success: boolean; historical_balances: any[]}>(response);
      if (responseData.success) {
        setHistoricalBalances(responseData.historical_balances || []);
      }
    } catch (err) {
      console.error('Error loading historical balances:', err);
      setError('Failed to load historical balances');
    } finally {
      setHistoricalBalancesLoading(false);
    }
  };
  
  const handleExportHistoricalBalancesExcel = () => {
    if (!selectedWallet || historicalBalances.length === 0) return;
    
    try {
      // Collect all unique tokens
      const allTokens = new Set<string>();
      historicalBalances.forEach(day => {
        Object.keys(day.balances || {}).forEach(token => allTokens.add(token));
      });
      const tokenList = Array.from(allTokens).sort();
      
      // Prepare data for Excel
      const excelData: any[][] = [];
      
      // Header row
      const header = ['Date', 'Total USD', ...tokenList.map(t => `${t} Amount`), ...tokenList.map(t => `${t} USD Value`)];
      excelData.push(header);
      
      // Data rows
      historicalBalances.forEach(day => {
        const row: any[] = [
          day.date,
          day.total_usd || 0
        ];
        
        // Add amounts for each token
        tokenList.forEach(token => {
          const balance = day.balances?.[token];
          row.push(balance?.amount || 0);
        });
        
        // Add USD values for each token
        tokenList.forEach(token => {
          const balance = day.balances?.[token];
          row.push(balance?.usd_value || 0);
        });
        
        excelData.push(row);
      });
      
      // Create workbook
      const worksheet = XLSX.utils.aoa_to_sheet(excelData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Historical Balances');
      
      // Generate filename
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `${selectedWallet.wallet_name}_historical_balances_${timestamp}.xlsx`;
      
      // Download
      XLSX.writeFile(workbook, filename);
    } catch (err) {
      console.error('Error exporting to Excel:', err);
      setError('Failed to export to Excel');
    }
  };

  const loadWalletTransactions = async (walletId: number) => {
    try {
      setWalletTransactionsLoading(true);
      
      // Fetch ALL transactions by paginating through all pages
      const allTransactions: TrustTransaction[] = [];
      let page = 1;
      let hasMore = true;
      const perPage = 100;
      
      while (hasMore) {
        const response = await api.get(`/trust-wallet/wallets/${walletId}/transactions?page=${page}&per_page=${perPage}`);
        const responseData = await api.parseResponse<{success: boolean; transactions: TrustTransaction[]; pagination: any}>(response);
        
        if (responseData.success && responseData.transactions) {
          allTransactions.push(...responseData.transactions);
          
          // Check if there are more pages
          const pagination = responseData.pagination;
          if (pagination && page < pagination.total_pages) {
            page++;
          } else {
            hasMore = false;
          }
        } else {
          hasMore = false;
        }
      }
      
      console.log(`Loaded ${allTransactions.length} total transactions for wallet ${walletId}`);
      setWalletTransactions(allTransactions);
    } catch (err) {
      console.error('Error loading wallet transactions:', err);
      setError('Failed to load wallet transactions');
    } finally {
      setWalletTransactionsLoading(false);
    }
  };

  const loadWalletBalance = async (walletId: number) => {
    try {
      setBalancesLoading(prev => ({...prev, [walletId]: true}));
      console.log('Loading balance for wallet:', walletId);
      const response = await api.get(`/trust-wallet/wallets/${walletId}/balance`);
      console.log('Balance response:', response);
      const responseData = await api.parseResponse<any>(response);
      console.log('Parsed balance data:', responseData);
      
      // Backend iki farklı format dönebilir:
      // 1. {success: true, data: {...}} formatı
      // 2. Direkt balance data'sı {...balances, total_usd, ...}
      if (responseData.success && responseData.data) {
        // Format 1: success wrapper ile
        setWalletBalances(prev => ({...prev, [walletId]: responseData.data}));
        console.log('Balance loaded successfully (format 1) for wallet', walletId);
      } else if (responseData.total_usd !== undefined || responseData.balances) {
        // Format 2: direkt balance data
        setWalletBalances(prev => ({...prev, [walletId]: responseData}));
        console.log('Balance loaded successfully (format 2) for wallet', walletId);
      } else {
        console.error('Balance load failed for wallet', walletId, '- unexpected format');
        setWalletBalances(prev => ({...prev, [walletId]: null}));
      }
    } catch (err) {
      console.error('Error loading wallet balance for wallet', walletId, ':', err);
      // Hata durumunda bile balance state'ini set et (boş olarak)
      setWalletBalances(prev => ({...prev, [walletId]: null}));
    } finally {
      setBalancesLoading(prev => ({...prev, [walletId]: false}));
    }
  };

  const handleCloseWalletModal = () => {
    setShowWalletModal(false);
    setSelectedWallet(null);
    setWalletTransactions([]);
    setHistoricalBalances([]);
    // Reset modal filters
    setModalSearchTerm('');
    setModalTypeFilter('all');
    setModalTokenFilter('all');
    setModalStatusFilter('all');
    setModalSortBy('date');
    setModalSortOrder('desc');
    setModalViewMode('detailed');
    setModalGroupByDay(false);
    setShowFilters(false);
    setCurrentPage(1);
    setTransactionsPerPage(50);
    setModalView('transactions');
    setHistoricalStartDate('');
    setHistoricalEndDate('');
  };

  const handleEditWallet = async (walletId: number) => {
    const wallet = wallets.find(w => w.id === walletId);
    if (wallet) {
      setEditingWallet(wallet);
      setShowEditModal(true);
    }
  };

  const handleSaveWalletEdit = async (walletName: string, isActive: boolean) => {
    if (!editingWallet) return;

    try {
      const response = await api.put(`/trust-wallet/wallets/${editingWallet.id}`, {
        wallet_name: walletName,
        is_active: isActive
      });
      const responseData = await api.parseResponse<{success: boolean}>(response);
      
      if (responseData.success) {
        // Update local state
        setWallets(prev => prev.map(w => 
          w.id === editingWallet.id 
            ? { ...w, wallet_name: walletName, is_active: isActive }
            : w
        ));
        setShowEditModal(false);
        setEditingWallet(null);
      }
    } catch (err) {
      console.error('Error updating wallet:', err);
      setError('Failed to update wallet');
    }
  };

  const handleDeleteWallet = (walletId: number) => {
    setDeletingWalletId(walletId);
    setShowDeleteModal(true);
    setDeleteSecurityCode('');
  };

  const confirmDeleteWallet = async () => {
    if (!deletingWalletId) return;
    
    // Check security code
    if (deleteSecurityCode !== '4561') {
      setError('Invalid security code. Please enter 4561');
      return;
    }
    
    // Prevent multiple deletion attempts
    if (deletingWallets.has(deletingWalletId)) {
      console.log('Wallet deletion already in progress for:', deletingWalletId);
      return;
    }
    
    try {
      setDeletingWallets(prev => new Set(prev).add(deletingWalletId));
      console.log('Deleting wallet:', deletingWalletId);
      
      const response = await api.delete(`/trust-wallet/wallets/${deletingWalletId}`);
      const responseData = await api.parseResponse<{success: boolean}>(response);
      
      console.log('Delete response:', responseData);
      
      if (responseData.success) {
        console.log('Wallet deleted successfully, updating local state...');
        // Update local state immediately instead of full refresh
        setWallets(prev => prev.filter(wallet => wallet.id !== deletingWalletId));
        setTransactions(prev => prev.filter(tx => tx.wallet_id !== deletingWalletId));
        
        // Refresh summary data
        await loadSummary();
        
        // Close modal
        setShowDeleteModal(false);
        setDeletingWalletId(null);
        setDeleteSecurityCode('');
      } else {
        console.error('Delete failed:', responseData);
        setError('Failed to delete wallet');
      }
    } catch (err) {
      console.error('Error deleting wallet:', err);
      // Check if it's a 404 error (wallet already deleted)
      if (err instanceof Error && err.message.includes('404')) {
        console.log('Wallet already deleted, updating local state...');
        setWallets(prev => prev.filter(wallet => wallet.id !== deletingWalletId));
        setTransactions(prev => prev.filter(tx => tx.wallet_id !== deletingWalletId));
        await loadSummary();
        
        // Close modal
        setShowDeleteModal(false);
        setDeletingWalletId(null);
        setDeleteSecurityCode('');
      } else {
        setError('Failed to delete wallet');
      }
    } finally {
      setDeletingWallets(prev => {
        const newSet = new Set(prev);
        newSet.delete(deletingWalletId);
        return newSet;
      });
    }
  };

  const handleAddWalletSuccess = async (walletId?: number) => {
    setShowAddModal(false);
    await loadAllData();
    
    // Otomatik sync - yeni eklenen cüzdan için işlemleri çek
    if (walletId) {
      console.log('Auto-syncing newly added wallet:', walletId);
      // Kısa bir gecikme ile sync başlat (UI güncellensin diye)
      setTimeout(() => {
        handleSyncWallet(walletId);
      }, 500);
    }
  };

  const handleRefreshAll = () => {
    loadAllData();
  };

  const handleSyncAllWallets = async () => {
    // Sync all wallets one by one
    for (const wallet of wallets) {
      if (wallet.is_active) {
        await handleSyncWallet(wallet.id);
      }
    }
  };

  // Modal helpers - filtered and sorted transactions
  const filteredAndSortedTransactions = useMemo(() => {
    let filtered = walletTransactions;

    // Search filter
    if (modalSearchTerm) {
      const search = modalSearchTerm.toLowerCase();
      filtered = filtered.filter(tx => 
        tx.transaction_hash.toLowerCase().includes(search) ||
        tx.token_symbol.toLowerCase().includes(search) ||
        tx.from_address.toLowerCase().includes(search) ||
        tx.to_address.toLowerCase().includes(search)
      );
    }

    // Type filter
    if (modalTypeFilter !== 'all') {
      filtered = filtered.filter(tx => tx.transaction_type === modalTypeFilter);
    }

    // Token filter
    if (modalTokenFilter !== 'all') {
      filtered = filtered.filter(tx => tx.token_symbol === modalTokenFilter);
    }

    // Status filter
    if (modalStatusFilter !== 'all') {
      filtered = filtered.filter(tx => tx.status === modalStatusFilter);
    }

    // Sorting
    filtered = [...filtered].sort((a, b) => {
      let comparison = 0;
      
      if (modalSortBy === 'date') {
        comparison = new Date(a.block_timestamp).getTime() - new Date(b.block_timestamp).getTime();
      } else if (modalSortBy === 'amount') {
        comparison = a.token_amount - b.token_amount;
      } else if (modalSortBy === 'gas') {
        comparison = (a.gas_fee || 0) - (b.gas_fee || 0);
      }

      return modalSortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [walletTransactions, modalSearchTerm, modalTypeFilter, modalTokenFilter, modalStatusFilter, modalSortBy, modalSortOrder]);

  // Get native token for network
  const getNativeToken = (network: string) => {
    switch (network) {
      case 'ETH': return 'ETH';
      case 'BSC': return 'BNB';
      case 'TRC': return 'TRX';
      default: return 'ETH';
    }
  };

  // Calculate stats
  const transactionStats = useMemo(() => {
    const totalIn = filteredAndSortedTransactions
      .filter(tx => tx.transaction_type === 'IN')
      .reduce((sum, tx) => sum + tx.token_amount, 0);
    
    const totalOut = filteredAndSortedTransactions
      .filter(tx => tx.transaction_type === 'OUT')
      .reduce((sum, tx) => sum + tx.token_amount, 0);
    
    const totalGas = filteredAndSortedTransactions.reduce((sum, tx) => sum + tx.gas_fee, 0);
    
    // Get the native token for the selected wallet
    const nativeToken = selectedWallet ? getNativeToken(selectedWallet.network) : 'ETH';
    
    return { totalIn, totalOut, totalGas, count: filteredAndSortedTransactions.length, nativeToken };
  }, [filteredAndSortedTransactions, selectedWallet]);

  // Get unique tokens for filter
  const uniqueTokens = useMemo(() => {
    return [...new Set(walletTransactions.map(tx => tx.token_symbol))].sort();
  }, [walletTransactions]);

  // Group transactions by day
  const groupedTransactionsByDay = useMemo(() => {
    if (!modalGroupByDay) return null;
    
    const groups: { [key: string]: TrustTransaction[] } = {};
    
    filteredAndSortedTransactions.forEach(tx => {
      const date = new Date(tx.block_timestamp).toISOString().split('T')[0];
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(tx);
    });
    
    return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a));
  }, [filteredAndSortedTransactions, modalGroupByDay]);

  // Pagination logic
  const paginatedTransactions = useMemo(() => {
    if (modalGroupByDay && groupedTransactionsByDay) {
      const startIndex = (currentPage - 1) * transactionsPerPage;
      const endIndex = startIndex + transactionsPerPage;
      const totalDays = groupedTransactionsByDay.length;
      const paginatedDays = groupedTransactionsByDay.slice(startIndex, endIndex);
      return { paginatedDays, totalDays, totalPages: Math.ceil(totalDays / transactionsPerPage) };
    } else {
      const startIndex = (currentPage - 1) * transactionsPerPage;
      const endIndex = startIndex + transactionsPerPage;
      const paginatedTxs = filteredAndSortedTransactions.slice(startIndex, endIndex);
      return { paginatedTxs, totalPages: Math.ceil(filteredAndSortedTransactions.length / transactionsPerPage), totalItems: filteredAndSortedTransactions.length };
    }
  }, [filteredAndSortedTransactions, modalGroupByDay, groupedTransactionsByDay, currentPage, transactionsPerPage]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [modalSearchTerm, modalTypeFilter, modalTokenFilter, modalStatusFilter]);

  // Export to CSV
  const handleExportCSV = () => {
    const csvHeader = 'Date,Type,Token,Amount,Gas Fee,Status,From,To,Hash\n';
    const csvRows = filteredAndSortedTransactions.map(tx => {
      return [
        new Date(tx.block_timestamp).toISOString(),
        tx.transaction_type,
        tx.token_symbol,
        tx.token_amount,
        tx.gas_fee || 0,
        tx.status,
        tx.from_address,
        tx.to_address,
        tx.transaction_hash
      ].join(',');
    }).join('\n');
    
    const blob = new Blob([csvHeader + csvRows], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedWallet?.wallet_name || 'wallet'}_transactions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Get block explorer URL
  const getBlockExplorerUrl = (hash: string, network: string) => {
    if (network === 'ETH') return `https://etherscan.io/tx/${hash}`;
    if (network === 'BSC') return `https://bscscan.com/tx/${hash}`;
    if (network === 'TRC') return `https://tronscan.org/#/transaction/${hash}`;
    return '';
  };

  // Copy to clipboard with fallback for insecure contexts
  const handleCopyToClipboard = async (text: string): Promise<boolean> => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      return true;
    } catch (err) {
      console.error('Failed to copy text:', err);
      return false;
    }
  };

  const handleCopyWalletAddress = async (
    event: React.MouseEvent<HTMLButtonElement>,
    walletId: number,
    address: string
  ) => {
    event.stopPropagation();
    const success = await handleCopyToClipboard(address);
    if (success) {
      setCopiedWalletId(walletId);
    }
  };

  // Calculate total USD balance across all wallets
  const totalBalanceSummary = useMemo(() => {
    let totalUSD = 0;
    let loadedWalletsCount = 0;
    const allBalancesLoaded = wallets.every(wallet => 
      walletBalances[wallet.id] && !balancesLoading[wallet.id]
    );

    wallets.forEach(wallet => {
      const balance = walletBalances[wallet.id];
      if (balance && balance.total_usd !== undefined) {
        totalUSD += balance.total_usd;
        loadedWalletsCount++;
      }
    });

    return {
      totalUSD,
      loadedWalletsCount,
      allBalancesLoaded,
      isLoading: wallets.length > 0 && !allBalancesLoaded
    };
  }, [wallets, walletBalances, balancesLoading]);

  // Filter wallets based on search and network
  const filteredWallets = wallets.filter(wallet => {
    const matchesSearch = wallet.wallet_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         wallet.wallet_address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesNetwork = networkFilter === 'all' || wallet.network === networkFilter;
    return matchesSearch && matchesNetwork;
  });

  // Get unique networks for filter
  const availableNetworks = [...new Set(wallets.map(w => w.network))];

  if (loading) {
    return (
      <div className="w-full bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        {/* Enhanced Header Skeleton */}
        <div className="mb-8 px-6 pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-lg animate-pulse"></div>
                <div>
                  <div className="h-8 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
                  <div className="h-4 bg-gray-200 rounded w-64 animate-pulse"></div>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="h-10 bg-gray-200 rounded-xl w-20 animate-pulse"></div>
              <div className="h-10 bg-gray-200 rounded-xl w-24 animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Enhanced Search Skeleton */}
        <div className="mb-8 px-6">
          <div className="h-12 bg-gray-200 rounded-xl w-80 animate-pulse"></div>
        </div>

        {/* Summary Card Skeleton */}
        <div className="mb-8 px-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 bg-gray-200 rounded-lg animate-pulse"></div>
              <div className="h-6 bg-gray-200 rounded w-40 animate-pulse"></div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg animate-pulse mb-3"></div>
                  <div className="space-y-2">
                    <div className="h-3 bg-gray-100 rounded w-20 animate-pulse"></div>
                    <div className="h-6 bg-gray-200 rounded w-24 animate-pulse"></div>
                    <div className="h-3 bg-gray-100 rounded w-28 animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Enhanced Wallets Skeleton */}
        <div className="px-6 pb-8">
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-2xl p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="w-12 h-12 bg-gray-200 rounded-lg animate-pulse flex-shrink-0"></div>
                    <div className="flex-1 min-w-0">
                      <div className="h-6 bg-gray-200 rounded w-32 mb-2 animate-pulse"></div>
                      <div className="h-4 bg-gray-200 rounded w-48 mb-3 animate-pulse"></div>
                      <div className="flex gap-2">
                        <div className="h-6 bg-gray-200 rounded-full w-16 animate-pulse"></div>
                        <div className="h-6 bg-gray-200 rounded-full w-12 animate-pulse"></div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0 ml-6">
                    <div className="h-10 bg-gray-200 rounded-xl w-16 animate-pulse"></div>
                    <div className="h-10 bg-gray-200 rounded-xl w-16 animate-pulse"></div>
                    <div className="h-10 bg-gray-200 rounded-xl w-20 animate-pulse"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      {/* Enhanced Header */}
      <div className="mb-8 px-6 pt-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <Wallet className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Trust Wallets
                </h1>
                <p className="text-gray-600 font-medium">Manage your blockchain wallets and transactions</p>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleRefreshAll}
              className="px-5 py-2.5 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors bg-white"
            >
              <RefreshCw className="h-4 w-4 inline mr-2" />
              Refresh
            </button>
            <button
              onClick={handleSyncAllWallets}
              disabled={syncingWallets.size > 0 || wallets.length === 0}
              className="px-5 py-2.5 text-sm font-medium border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 transition-colors bg-white disabled:opacity-50 disabled:cursor-not-allowed"
              title={wallets.length === 0 ? "No wallets to sync" : "Sync all wallets"}
            >
              <RefreshCw className={`h-4 w-4 inline mr-2 ${syncingWallets.size > 0 ? 'animate-spin' : ''}`} />
              Sync All {syncingWallets.size > 0 && `(${syncingWallets.size}/${wallets.length})`}
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="group px-6 py-2.5 text-sm font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md"
            >
              <Plus className="h-4 w-4 inline mr-2" />
              Add Wallet
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center mr-3">
                <AlertCircle className="h-4 w-4 text-red-600" />
              </div>
              <span className="text-red-800 font-medium">{error}</span>
              <button
                onClick={() => setError(null)}
                className="ml-auto w-6 h-6 bg-red-100 hover:bg-red-200 rounded-lg flex items-center justify-center text-red-600 hover:text-red-700 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Search and Filter */}
      <div className="mb-8 px-6">
        <div className="flex gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[280px]">
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search wallets by name or address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none bg-white shadow-sm transition-colors"
            />
          </div>
          <div className="relative min-w-[180px]">
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
              <Filter className="h-4 w-4 text-gray-400" />
            </div>
            <select
              value={networkFilter}
              onChange={(e) => setNetworkFilter(e.target.value)}
              className="w-full pl-12 pr-10 py-3 border border-gray-200 rounded-lg focus:outline-none bg-white shadow-sm transition-colors appearance-none cursor-pointer text-sm font-medium text-gray-700"
            >
              <option value="all">All Networks</option>
              {availableNetworks.map(network => (
                <option key={network} value={network}>{network}</option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Portfolio Summary - Unified Design */}
      <div className="mb-8 px-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          {/* Header */}
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
              <Wallet className="h-4 w-4 text-gray-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Portfolio Summary</h2>
          </div>
          
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total USD Balance */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                {totalBalanceSummary.isLoading && (
                  <RefreshCw className="h-4 w-4 text-gray-400 animate-spin" />
                )}
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Total Balance</p>
                {totalBalanceSummary.isLoading ? (
                  <div className="h-7 bg-gray-100 rounded animate-pulse w-28"></div>
                ) : (
                  <p className="text-lg font-semibold text-gray-900">
                    ${totalBalanceSummary.totalUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                )}
                <p className="text-xs text-gray-500">Across all wallets</p>
              </div>
            </div>

            {/* Active Wallets */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                  <Wallet className="h-5 w-5 text-purple-600" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Active Wallets</p>
                <p className="text-lg font-semibold text-gray-900">
                  {wallets.filter(w => w.is_active).length}
                </p>
                <p className="text-xs text-gray-500">
                  {totalBalanceSummary.loadedWalletsCount} with loaded balances
                </p>
              </div>
            </div>

            {/* Total Transactions */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                  <Activity className="h-5 w-5 text-blue-600" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Total Transactions</p>
                <p className="text-lg font-semibold text-gray-900">
                  {summary?.overall?.total_transactions?.toLocaleString() || 0}
                </p>
                <p className="text-xs text-gray-500">All networks</p>
              </div>
            </div>

            {/* Active Networks */}
            <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center">
                  <Layers className="h-5 w-5 text-orange-600" />
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">Active Networks</p>
                <p className="text-lg font-semibold text-gray-900">
                  {availableNetworks.length}
                </p>
                <p className="text-xs text-gray-500">
                  {availableNetworks.join(', ') || 'None'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Wallets Grid - Professional Design */}
      <div className="px-6 pb-8">
        {filteredWallets.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredWallets.map(wallet => {
              const balance = walletBalances[wallet.id];
              const totalUSD = balance?.total_usd || 0;
              const isLoading = balancesLoading[wallet.id];
              const tokenCount = balance ? Object.keys(balance.balances || {}).length : 0;
              
              return (
                <div
                  key={wallet.id}
                  onClick={() => handleViewWallet(wallet.id)}
                  className="cursor-pointer group"
                >
                  <UnifiedCard
                    variant="outlined"
                    className="hover:shadow-xl hover:border-gray-400 transition-all duration-300 relative overflow-hidden h-full bg-white"
                  >
                    {/* Premium gradient overlay on hover */}
                    <div className="absolute inset-0 bg-gradient-to-br from-slate-50/0 via-transparent to-blue-50/0 group-hover:from-slate-50/40 group-hover:to-blue-50/20 transition-all duration-500 pointer-events-none" />
                    
                    <div className="relative space-y-6 p-6">
                      {/* Header with enhanced spacing */}
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-3.5 flex-1 min-w-0">
                          <div className="w-12 h-12 bg-gradient-to-br from-slate-100 via-gray-50 to-slate-100 rounded-xl flex items-center justify-center flex-shrink-0 border border-gray-300 shadow-md group-hover:shadow-lg group-hover:scale-105 transition-all duration-300">
                            <Wallet className="h-6 w-6 text-gray-700" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-bold text-gray-900 text-lg truncate group-hover:text-black transition-colors">{wallet.wallet_name}</h3>
                            <div className="flex items-center gap-2 mt-1.5">
                              <p className="text-xs text-gray-500 font-mono truncate bg-gray-50 px-2 py-0.5 rounded border border-gray-200">
                                {wallet.wallet_address.slice(0, 10)}...{wallet.wallet_address.slice(-8)}
                              </p>
                              <button
                                onClick={(e) => handleCopyWalletAddress(e, wallet.id, wallet.wallet_address)}
                                className="opacity-0 group-hover:opacity-100 transition-all duration-200 p-1 hover:bg-gray-100 rounded border border-transparent hover:border-gray-300"
                                title={copiedWalletId === wallet.id ? 'Address copied!' : 'Copy full address'}
                              >
                                {copiedWalletId === wallet.id ? (
                                  <Check className="h-3.5 w-3.5 text-green-600" />
                                ) : (
                                  <Copy className="h-3.5 w-3.5 text-gray-400 hover:text-gray-700" />
                                )}
                              </button>
                            </div>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                          <UnifiedBadge variant="outline" size="sm" className="text-xs font-semibold px-2.5 py-1">
                            {wallet.network}
                          </UnifiedBadge>
                          {wallet.is_active && (
                            <UnifiedBadge variant="success" size="sm" className="text-xs font-semibold px-2.5 py-1">
                              <div className="w-2 h-2 bg-green-500 rounded-full mr-1.5 animate-pulse shadow-sm shadow-green-500/50" />
                              Active
                            </UnifiedBadge>
                          )}
                        </div>
                      </div>

                      {/* Total Balance - Prominent Display with better visual hierarchy */}
                      <div className="pt-5 border-t border-gray-300">
                        <div className="flex items-baseline justify-between mb-3">
                          <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total Balance</span>
                          {balance?.last_updated && (
                            <div className="flex items-center gap-1.5 text-xs text-gray-400 bg-gray-50 px-2 py-1 rounded-md border border-gray-200">
                              <Clock className="h-3 w-3" />
                              <span>
                                {new Date(balance.last_updated).toLocaleTimeString('en-US', { 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </span>
                            </div>
                          )}
                        </div>
                        {isLoading ? (
                          <div className="flex items-center gap-3 mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <RefreshCw className="h-5 w-5 text-gray-400 animate-spin" />
                            <span className="text-sm font-medium text-gray-500">Loading balance...</span>
                          </div>
                        ) : balance && totalUSD > 0 ? (
                          <div className="mt-2">
                            <p className="text-4xl font-extrabold text-gray-900 tracking-tight">
                              ${totalUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                            {tokenCount > 0 && (
                              <p className="text-xs font-medium text-gray-500 mt-2 flex items-center gap-1.5">
                                <DollarSign className="h-3 w-3" />
                                {tokenCount} asset{tokenCount !== 1 ? 's' : ''}
                              </p>
                            )}
                          </div>
                        ) : balance ? (
                          <div className="mt-2">
                            <p className="text-3xl font-bold text-gray-400">$0.00</p>
                            <p className="text-xs text-gray-500 mt-2">No balance</p>
                          </div>
                        ) : balance === null ? (
                          <div className="mt-2">
                            <p className="text-sm font-medium text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-200 flex items-center gap-2">
                              <AlertCircle className="h-4 w-4" />
                              Failed to load balance
                            </p>
                          </div>
                        ) : (
                          <div className="mt-2">
                            <p className="text-sm font-medium text-gray-500 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200">
                              Sync wallet to see balance
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Token Balances - Enhanced Grid */}
                      {balance && tokenCount > 0 && (
                        <div className="pt-5 border-t border-gray-300">
                          <div className="grid grid-cols-2 gap-3">
                            {Object.entries(balance.balances || {}).slice(0, 4).map(([token, balanceData]: [string, any]) => {
                              const amount = typeof balanceData === 'number' ? balanceData : balanceData.amount;
                              const usdValue = typeof balanceData === 'object' && balanceData.usd_value ? balanceData.usd_value : null;
                              const displayAmount = Number(amount);
                              
                              return (
                                <div key={token} className="relative bg-white border-2 border-gray-200 rounded-xl p-3 hover:border-gray-400 hover:shadow-md transition-all duration-200 group/token">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-bold text-gray-600 uppercase tracking-wider">{token}</span>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="text-base font-extrabold text-gray-900 truncate" title={String(amount)}>
                                      {displayAmount >= 0.0001 
                                        ? displayAmount.toLocaleString('en-US', { maximumFractionDigits: 6, minimumFractionDigits: 0 })
                                        : displayAmount.toExponential(2)
                                      }
                                    </div>
                                    {usdValue !== null && usdValue !== undefined && usdValue > 0 && (
                                      <div className="text-xs font-semibold text-gray-600 flex items-center gap-1">
                                        <span className="text-gray-400">≈</span>
                                        ${usdValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                          {tokenCount > 4 && (
                            <div className="mt-4 pt-3 border-t border-gray-200">
                              <p className="text-xs font-semibold text-gray-600 text-center bg-gray-50 py-2 rounded-lg border border-gray-200">
                                +{tokenCount - 4} more asset{tokenCount - 4 !== 1 ? 's' : ''}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Actions - Enhanced Footer */}
                      <div className="pt-5 border-t border-gray-300 flex items-center justify-between">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSyncWallet(wallet.id);
                          }}
                          disabled={syncingWallets.has(wallet.id)}
                          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-gray-700 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-gray-200 hover:border-blue-300 shadow-sm hover:shadow"
                          title="Sync wallet transactions"
                        >
                          <RefreshCw className={`h-4 w-4 ${syncingWallets.has(wallet.id) ? 'animate-spin' : ''}`} />
                          <span>{syncingWallets.has(wallet.id) ? 'Syncing...' : 'Sync'}</span>
                        </button>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditWallet(wallet.id);
                            }}
                            className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all border border-transparent hover:border-gray-300"
                            title="Edit wallet"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewWallet(wallet.id);
                            }}
                            className="p-2 text-gray-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all border border-transparent hover:border-blue-300"
                            title="View details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteWallet(wallet.id);
                            }}
                            disabled={deletingWallets.has(wallet.id)}
                            className="p-2 text-gray-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-transparent hover:border-red-300"
                            title="Delete wallet"
                          >
                            {deletingWallets.has(wallet.id) ? (
                              <RefreshCw className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </UnifiedCard>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-20">
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-6">
              <Wallet className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              {wallets.length === 0 ? 'No wallets connected' : 'No wallets found'}
            </h3>
            <p className="text-gray-600 max-w-md mx-auto text-lg leading-relaxed">
              {wallets.length === 0 
                ? 'Get started by adding your first wallet to monitor blockchain transactions and balances.' 
                : 'Try adjusting your search criteria to find the wallets you\'re looking for.'
              }
            </p>
            {wallets.length === 0 && (
              <button
                onClick={() => setShowAddModal(true)}
                className="mt-8 px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-base font-semibold shadow-sm"
              >
                <Plus className="h-5 w-5 inline mr-2" />
                Add Your First Wallet
              </button>
            )}
          </div>
        )}
      </div>

      {/* Add Wallet Modal */}
      <AddWalletModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={handleAddWalletSuccess}
      />

      {/* Edit Wallet Modal */}
      {showEditModal && editingWallet && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">Edit Wallet</h2>
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingWallet(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              const walletName = formData.get('wallet_name') as string;
              const isActive = formData.get('is_active') === 'on';
              handleSaveWalletEdit(walletName, isActive);
            }}>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wallet Name
                  </label>
                  <input
                    type="text"
                    name="wallet_name"
                    defaultValue={editingWallet.wallet_name}
                    required
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none"
                    placeholder="Enter wallet name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Wallet Address
                  </label>
                  <input
                    type="text"
                    value={editingWallet.wallet_address}
                    disabled
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                  />
                  <p className="mt-1 text-xs text-gray-500">Wallet address cannot be changed</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Network
                  </label>
                  <input
                    type="text"
                    value={editingWallet.network}
                    disabled
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_active"
                    id="is_active"
                    defaultChecked={editingWallet.is_active}
                    className="h-4 w-4 text-blue-600 focus:outline-none border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 text-sm font-medium text-gray-700">
                    Active
                  </label>
                </div>
              </div>
              <div className="p-6 border-t border-gray-200 flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingWallet(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Save className="h-4 w-4 inline mr-1.5" />
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Wallet Modal */}
      {showDeleteModal && deletingWalletId && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  </div>
                  <h2 className="text-lg font-semibold text-gray-900">Delete Wallet</h2>
                </div>
                <button
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeletingWalletId(null);
                    setDeleteSecurityCode('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  You are about to delete the wallet: <span className="font-semibold">{wallets.find(w => w.id === deletingWalletId)?.wallet_name}</span>
                </p>
                <p className="text-sm text-red-700 mt-2">
                  This action cannot be undone. All transaction history will be permanently deleted.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Security Code
                </label>
                <p className="text-xs text-gray-500 mb-2">Enter security code to confirm deletion</p>
                <input
                  type="text"
                  value={deleteSecurityCode}
                  onChange={(e) => setDeleteSecurityCode(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 text-center font-mono text-lg tracking-wider"
                  placeholder="Enter code"
                  autoFocus
                  maxLength={4}
                />
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeletingWalletId(null);
                  setDeleteSecurityCode('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteWallet}
                disabled={deletingWallets.has(deletingWalletId)}
                className="px-4 py-2 text-sm font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deletingWallets.has(deletingWalletId) ? (
                  <>
                    <RefreshCw className="h-4 w-4 inline mr-1.5 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4 inline mr-1.5" />
                    Delete Wallet
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Wallet Transactions Modal */}
      {showWalletModal && selectedWallet && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-lg max-w-7xl w-full max-h-[95vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-white">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-gray-50 flex items-center justify-center">
                  <Wallet className="h-5 w-5 text-gray-700" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{selectedWallet.wallet_name}</h2>
                  <p className="text-sm text-gray-500 font-mono truncate max-w-md mt-0.5">{selectedWallet.wallet_address}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2.5 py-1 rounded border border-gray-200">
                      {selectedWallet.network}
                    </span>
                    {selectedWallet.is_active && (
                  <span className="text-xs font-medium text-gray-700 bg-gray-50 px-2.5 py-1 rounded border border-gray-200">
                        Active
                      </span>
                    )}
                <button
                  onClick={handleCloseWalletModal}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
                  </div>
                </div>

            {/* Tabs */}
            <div className="flex items-center gap-2 px-6 pt-6 border-b border-gray-200 bg-white">
              <button
                onClick={() => {
                  setModalView('transactions');
                }}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  modalView === 'transactions'
                    ? 'bg-white border-t border-x border-gray-200 text-gray-900'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Activity className="h-4 w-4 inline mr-2" />
                Transactions
              </button>
              <button
                onClick={() => {
                  setModalView('historical');
                  // Always load historical balances when switching to this tab
                  // Clear date filters to fetch from wallet birth
                  if (selectedWallet) {
                    setHistoricalStartDate('');
                    setHistoricalEndDate('');
                    loadHistoricalBalances(selectedWallet.id);
                  }
                }}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                  modalView === 'historical'
                    ? 'bg-white border-t border-x border-gray-200 text-gray-900'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <History className="h-4 w-4 inline mr-2" />
                Historical Balances
              </button>
            </div>

            {/* Toolbar - Only show for transactions view */}
            {modalView === 'transactions' && (
              <div className="p-6 bg-white border-b border-gray-200 space-y-4">
                {/* Search and Controls Row */}
                <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search transactions..."
                        value={modalSearchTerm}
                        onChange={(e) => setModalSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none bg-white text-sm"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                <button
                      onClick={() => setShowFilters(!showFilters)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        showFilters ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                      } border border-gray-200`}
                    >
                      <Filter className="h-4 w-4 inline mr-1.5" />
                      Filters
                    </button>
                    <button
                      onClick={() => setModalGroupByDay(!modalGroupByDay)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        modalGroupByDay ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                      } border border-gray-200`}
                    >
                      <Layers className="h-4 w-4 inline mr-1.5" />
                      {modalGroupByDay ? 'Ungroup' : 'Group'}
                    </button>
                    <button
                      onClick={handleExportCSV}
                      className="px-4 py-2 bg-white text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 border border-gray-200 transition-colors"
                    >
                      <Download className="h-4 w-4 inline mr-1.5" />
                      Export
                    </button>
                    <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-lg p-1">
                      <button
                        onClick={() => setModalViewMode('compact')}
                        className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                          modalViewMode === 'compact' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'
                        }`}
                      >
                        <Grid className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setModalViewMode('detailed')}
                        className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                          modalViewMode === 'detailed' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'
                        }`}
                      >
                        <List className="h-4 w-4" />
                </button>
                    </div>
                  </div>
              </div>

                {/* Filters Panel */}
                {showFilters && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 pt-4 border-t border-gray-200">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-2">Type</label>
                    <select
                      value={modalTypeFilter}
                      onChange={(e) => setModalTypeFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none"
                    >
                      <option value="all">All</option>
                      <option value="IN">Inbound</option>
                      <option value="OUT">Outbound</option>
                      <option value="INTERNAL">Internal</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-2">Token</label>
                    <select
                      value={modalTokenFilter}
                      onChange={(e) => setModalTokenFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none"
                    >
                      <option value="all">All</option>
                      {uniqueTokens.map(token => (
                        <option key={token} value={token}>{token}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-2">Status</label>
                    <select
                      value={modalStatusFilter}
                      onChange={(e) => setModalStatusFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none"
                    >
                      <option value="all">All</option>
                      <option value="CONFIRMED">Confirmed</option>
                      <option value="PENDING">Pending</option>
                      <option value="FAILED">Failed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-2">Sort By</label>
                    <div className="flex gap-2">
                      <select
                        value={modalSortBy}
                        onChange={(e) => setModalSortBy(e.target.value as 'date' | 'amount' | 'gas')}
                        className="flex-1 px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none"
                      >
                        <option value="date">Date</option>
                        <option value="amount">Amount</option>
                        <option value="gas">Gas Fee</option>
                      </select>
                      <button
                        onClick={() => setModalSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                        className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-100"
                      >
                        {modalSortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
                )}
              </div>
            )}

            {/* Content - Transactions or Historical Balances */}
            <div className="overflow-y-auto bg-white flex-1">
              {modalView === 'historical' ? (
                // Historical Balances View
                <div className="p-6">
                  {/* Info Banner */}
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-blue-900">
                          {historicalStartDate || historicalEndDate 
                            ? 'Showing filtered historical balances'
                            : 'Showing complete wallet history'
                          }
                        </p>
                        <p className="text-xs text-blue-700 mt-1">
                          {historicalStartDate || historicalEndDate
                            ? `Date range: ${historicalStartDate || 'Wallet birth'} to ${historicalEndDate || 'Today'}`
                            : 'Displaying all balances from wallet creation to today. Use date filters to narrow results.'
                          }
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Date Range Filters */}
                  <div className="mb-6 flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-700 mb-2">
                        Start Date <span className="text-gray-500 font-normal">(Optional - defaults to wallet birth)</span>
                      </label>
                      <input
                        type="date"
                        value={historicalStartDate}
                        onChange={(e) => setHistoricalStartDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-700 mb-2">
                        End Date <span className="text-gray-500 font-normal">(Optional - defaults to today)</span>
                      </label>
                      <input
                        type="date"
                        value={historicalEndDate}
                        onChange={(e) => setHistoricalEndDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <button
                      onClick={() => selectedWallet && loadHistoricalBalances(selectedWallet.id)}
                      disabled={historicalBalancesLoading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
                    >
                      <RefreshCw className={`h-4 w-4 inline mr-2 ${historicalBalancesLoading ? 'animate-spin' : ''}`} />
                      {historicalBalancesLoading ? 'Loading...' : 'Refresh'}
                    </button>
                    <button
                      onClick={handleExportHistoricalBalancesExcel}
                      disabled={historicalBalances.length === 0}
                      className="px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 border border-gray-200 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Download className="h-4 w-4 inline mr-2" />
                      Export Excel
                    </button>
                  </div>

                  {/* Historical Balances Table */}
                  {historicalBalancesLoading ? (
                    <div className="flex items-center justify-center py-20">
                      <div className="text-center">
                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                          <RefreshCw className="h-6 w-6 animate-spin text-gray-600" />
                        </div>
                        <span className="text-lg font-medium text-gray-600">Loading historical balances...</span>
                      </div>
                    </div>
                  ) : historicalBalances.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Date</th>
                            <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">Total USD</th>
                            {(() => {
                              const allTokens = new Set<string>();
                              historicalBalances.forEach(day => {
                                Object.keys(day.balances || {}).forEach(token => allTokens.add(token));
                              });
                              return Array.from(allTokens).sort().map(token => (
                                <React.Fragment key={token}>
                                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">{token} Amount</th>
                                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">{token} USD</th>
                                </React.Fragment>
                              ));
                            })()}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {historicalBalances.map((day, idx) => {
                            const allTokens = new Set<string>();
                            historicalBalances.forEach(d => {
                              Object.keys(d.balances || {}).forEach(token => allTokens.add(token));
                            });
                            const tokenList = Array.from(allTokens).sort();
                            
                            return (
                              <tr key={day.date || idx} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                                  {new Date(day.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                                </td>
                                <td className="px-4 py-3 text-sm font-semibold text-gray-900 text-right">
                                  ${(day.total_usd || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </td>
                                {tokenList.map(token => {
                                  const balance = day.balances?.[token];
                                  return (
                                    <React.Fragment key={token}>
                                      <td className="px-4 py-3 text-sm text-gray-700 text-right">
                                        {(balance?.amount || 0).toLocaleString('en-US', { maximumFractionDigits: 6 })}
                                      </td>
                                      <td className="px-4 py-3 text-sm text-gray-600 text-right">
                                        ${(balance?.usd_value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                      </td>
                                    </React.Fragment>
                                  );
                                })}
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-20">
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                        <History className="h-6 w-6 text-gray-400" />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">No historical balances found</h3>
                      <p className="text-sm text-gray-600">
                        Select a date range and click "Load" to view historical balances.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                // Transactions View
                <>
              {walletTransactionsLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <RefreshCw className="h-6 w-6 animate-spin text-gray-600" />
                    </div>
                    <span className="text-lg font-medium text-gray-600">Loading transactions...</span>
                  </div>
                </div>
              ) : filteredAndSortedTransactions.length > 0 ? (
                modalGroupByDay && paginatedTransactions.paginatedDays ? (
                  // Grouped by day view
                  <div className="space-y-6">
                    {paginatedTransactions.paginatedDays.map(([date, transactions]) => {
                      const dayTotalIn = transactions
                        .filter(tx => tx.transaction_type === 'IN')
                        .reduce((sum, tx) => sum + tx.token_amount, 0);
                      const dayTotalOut = transactions
                        .filter(tx => tx.transaction_type === 'OUT')
                        .reduce((sum, tx) => sum + tx.token_amount, 0);
                      const dayTotal = dayTotalIn - dayTotalOut;
                      
                      return (
                        <div key={date}>
                          {/* Day Header */}
                          <div className="mb-4 pb-3 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                              <div>
                                <h3 className="text-base font-semibold text-gray-900">{new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</h3>
                                <p className="text-xs text-gray-500 mt-0.5">{transactions.length} transaction{transactions.length !== 1 ? 's' : ''}</p>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-gray-500 uppercase tracking-wide">Net Flow</div>
                                <div className={`text-base font-semibold ${dayTotal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {dayTotal.toLocaleString(undefined, { maximumFractionDigits: 6 })}
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Transactions for this day */}
                          <div className="space-y-2 pl-2 border-l border-gray-200">
                            {transactions.map(transaction => {
                              const isCompact = modalViewMode === 'compact';
                              const explorerUrl = getBlockExplorerUrl(transaction.transaction_hash, transaction.network);
                              
                              return (
                    <div key={transaction.id} className={`bg-white border border-gray-200 hover:border-gray-300 transition-colors ${isCompact ? 'p-3' : 'p-4'}`}>
                      <div className="flex items-start justify-between gap-4">
                        {/* Main Content */}
                        <div className="flex items-start gap-3 flex-1 min-w-0">
                          {/* Icon */}
                          <div className={`bg-white rounded-lg flex items-center justify-center border-2 shadow-sm flex-shrink-0 ${isCompact ? 'w-10 h-10' : 'w-12 h-12'}`}>
                            {transaction.transaction_type === 'IN' ? (
                              <TrendingUp className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} text-green-600`} />
                            ) : transaction.transaction_type === 'OUT' ? (
                              <TrendingDown className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} text-red-600`} />
                            ) : (
                              <RotateCcw className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} text-blue-600`} />
                            )}
                          </div>
                          
                          {/* Transaction Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <span className={`font-bold text-gray-900 ${isCompact ? 'text-base' : 'text-lg'}`}>
                                {transaction.token_amount} {transaction.token_symbol}
                              </span>
                              <span className={`px-2 py-1 rounded-md font-medium text-xs ${
                                transaction.transaction_type === 'IN' ? 'bg-green-100 text-green-700' :
                                transaction.transaction_type === 'OUT' ? 'bg-red-100 text-red-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {transaction.transaction_type}
                              </span>
                              <span className={`px-2 py-1 rounded-md font-medium text-xs ${
                                transaction.status === 'CONFIRMED' ? 'bg-green-100 text-green-700' :
                                transaction.status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {transaction.status}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500 flex-wrap">
                              <span>{new Date(transaction.block_timestamp).toLocaleString()}</span>
                              {!isCompact && (
                                <>
                                  <span className="text-gray-300">•</span>
                                  <span className="text-xs font-mono truncate max-w-[150px]" title={transaction.transaction_hash}>
                                    {transaction.transaction_hash.slice(0, 16)}...
                                  </span>
                                </>
                              )}
                          </div>
                            {!isCompact && (
                              <div className="mt-3 grid grid-cols-2 gap-3">
                                <div>
                                  <span className="text-xs font-semibold text-gray-700 block mb-1">From:</span>
                                  <div className="font-mono text-xs text-gray-600 bg-gray-50 px-2 py-1.5 rounded break-all">{transaction.from_address}</div>
                        </div>
                                <div>
                                  <span className="text-xs font-semibold text-gray-700 block mb-1">To:</span>
                                  <div className="font-mono text-xs text-gray-600 bg-gray-50 px-2 py-1.5 rounded break-all">{transaction.to_address}</div>
                            </div>
                            </div>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-start gap-2 flex-shrink-0">
                          {!isCompact && transaction.gas_fee && transaction.gas_fee > 0 && (
                            <div className="text-right mr-4">
                              <div className="text-xs font-semibold text-gray-700 mb-1">Gas</div>
                              <div className="text-sm font-medium text-gray-900">
                                {transaction.gas_fee} {transaction.gas_fee_token}
                              </div>
                            </div>
                          )}
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleCopyToClipboard(transaction.transaction_hash)}
                              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                              title="Copy hash"
                            >
                              <Copy className="h-4 w-4 text-gray-500" />
                            </button>
                            {explorerUrl && (
                              <a
                                href={explorerUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="View on block explorer"
                              >
                                <ExternalLink className="h-4 w-4 text-gray-500" />
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                  })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  // Ungrouped view
                  <div className="space-y-2">
                    {paginatedTransactions.paginatedTxs?.map(transaction => {
                      const isCompact = modalViewMode === 'compact';
                      const explorerUrl = getBlockExplorerUrl(transaction.transaction_hash, transaction.network);
                      
                      return (
                    <div key={transaction.id} className={`bg-white border border-gray-200 hover:border-gray-300 transition-colors ${isCompact ? 'p-3' : 'p-4'}`}>
                      <div className="flex items-start justify-between gap-4">
                        {/* Main Content */}
                        <div className="flex items-start gap-3 flex-1 min-w-0">
                          {/* Icon */}
                          <div className={`bg-white rounded-lg flex items-center justify-center border-2 shadow-sm flex-shrink-0 ${isCompact ? 'w-10 h-10' : 'w-12 h-12'}`}>
                            {transaction.transaction_type === 'IN' ? (
                              <TrendingUp className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} text-green-600`} />
                            ) : transaction.transaction_type === 'OUT' ? (
                              <TrendingDown className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} text-red-600`} />
                            ) : (
                              <RotateCcw className={`${isCompact ? 'h-5 w-5' : 'h-6 w-6'} text-blue-600`} />
                            )}
                            </div>
                          
                          {/* Transaction Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <div>
                                <div className={`font-bold text-gray-900 ${isCompact ? 'text-base' : 'text-lg'}`}>
                                  {transaction.token_amount} {transaction.token_symbol}
                                </div>
                                {transaction.token_name && transaction.token_name !== transaction.token_symbol && (
                                  <div className="text-xs text-gray-500">
                                    {transaction.token_name}
                                  </div>
                                )}
                              </div>
                              <span className={`px-2 py-1 rounded-md font-medium text-xs ${
                                transaction.transaction_type === 'IN' ? 'bg-green-100 text-green-700' :
                                transaction.transaction_type === 'OUT' ? 'bg-red-100 text-red-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {transaction.transaction_type}
                              </span>
                              <span className={`px-2 py-1 rounded-md font-medium text-xs ${
                                transaction.status === 'CONFIRMED' ? 'bg-green-100 text-green-700' :
                                transaction.status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {transaction.status}
                          </span>
                        </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500 flex-wrap">
                              <span>{new Date(transaction.block_timestamp).toLocaleString()}</span>
                              {!isCompact && (
                                <>
                                  <span className="text-gray-300">•</span>
                                  <span className="text-xs font-mono truncate max-w-[150px]" title={transaction.transaction_hash}>
                                    {transaction.transaction_hash.slice(0, 16)}...
                                  </span>
                                </>
                              )}
                      </div>
                            {!isCompact && (
                              <div className="mt-3 grid grid-cols-2 gap-3">
                          <div>
                                  <span className="text-xs font-semibold text-gray-700 block mb-1">From:</span>
                                  <div className="font-mono text-xs text-gray-600 bg-gray-50 px-2 py-1.5 rounded break-all">{transaction.from_address}</div>
                          </div>
                          <div>
                                  <span className="text-xs font-semibold text-gray-700 block mb-1">To:</span>
                                  <div className="font-mono text-xs text-gray-600 bg-gray-50 px-2 py-1.5 rounded break-all">{transaction.to_address}</div>
                          </div>
                        </div>
                            )}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-start gap-2 flex-shrink-0">
                          {!isCompact && transaction.gas_fee && transaction.gas_fee > 0 && (
                            <div className="text-right mr-4">
                              <div className="text-xs font-semibold text-gray-700 mb-1">Gas</div>
                              <div className="text-sm font-medium text-gray-900">
                              {transaction.gas_fee} {transaction.gas_fee_token}
                              </div>
                          </div>
                          )}
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleCopyToClipboard(transaction.transaction_hash)}
                              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                              title="Copy hash"
                            >
                              <Copy className="h-4 w-4 text-gray-500" />
                            </button>
                            {explorerUrl && (
                              <a
                                href={explorerUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="View on block explorer"
                              >
                                <ExternalLink className="h-4 w-4 text-gray-500" />
                              </a>
                        )}
                      </div>
                    </div>
                </div>
                            </div>
                  );
                  })}
                  </div>
                )
              ) : (
                  <div className="text-center py-20">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <Wallet className="h-6 w-6 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No transactions found</h3>
                    <p className="text-sm text-gray-600">
                      {walletTransactions.length === 0 
                        ? "This wallet doesn't have any transactions yet."
                        : "No transactions match your filters. Try adjusting your search or filters."}
                    </p>
                  </div>
              )}

              {/* Pagination Controls */}
              {filteredAndSortedTransactions.length > 0 && paginatedTransactions.totalPages > 1 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-6 bg-white border-t border-gray-200">
                  <div className="flex items-center gap-2">
                    <label className="text-xs sm:text-sm text-gray-600">Per page:</label>
                    <select 
                      value={transactionsPerPage} 
                      onChange={(e) => {
                        setTransactionsPerPage(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="px-3 py-1.5 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none"
                    >
                      <option value="25">25</option>
                      <option value="50">50</option>
                      <option value="100">100</option>
                      <option value="200">200</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-2 border border-gray-200 rounded-lg bg-white text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm font-medium"
                    >
                      Prev
                    </button>
                    <div className="text-xs sm:text-sm text-gray-600 whitespace-nowrap">
                      Page {currentPage} of {paginatedTransactions.totalPages}
                    </div>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(paginatedTransactions.totalPages, prev + 1))}
                      disabled={currentPage === paginatedTransactions.totalPages}
                      className="px-3 py-2 border border-gray-200 rounded-lg bg-white text-gray-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm font-medium"
                    >
                      Next
                    </button>
                  </div>
                          </div>
              )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrustTabContent;

