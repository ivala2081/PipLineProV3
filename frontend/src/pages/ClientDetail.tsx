import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { 
  UnifiedCard, 
  UnifiedButton, 
  UnifiedBadge, 
  UnifiedSection, 
  UnifiedGrid 
} from '../design-system';
import { 
  ArrowLeft, 
  Edit,
  RefreshCw
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../hooks/useNotifications';
import { api } from '../utils/apiClient';
import { formatCurrency } from '../utils/currencyUtils';
import { logger } from '../utils/logger';
import { Breadcrumb } from '../components/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

interface ClientDetails {
  client_name: string;
  company_name?: string;
  statistics: {
    transaction_count: number;
    total_amount: number;
    total_commission: number;
    total_net: number;
    total_deposits: number;
    total_withdrawals: number;
    avg_transaction: number;
    first_transaction: string;
    last_transaction: string;
  };
  metadata: {
    currencies: string[];
    psps: string[];
    payment_methods: string[];
    categories: string[];
  };
  transactions: Array<{
    id: number;
    date: string;
    amount: number;
    currency: string;
    category: string;
    psp: string;
    payment_method: string;
    commission: number;
    net_amount: number;
    company?: string;
    notes?: string;
  }>;
}

export default function ClientDetail() {
  const { clientName } = useParams<{ clientName: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { success, error } = useNotifications();
  
  const [clientDetails, setClientDetails] = useState<ClientDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'transactions'>('overview');
  
  // Get client name from URL params or query string
  const getClientName = () => {
    if (clientName) {
      try {
        // Decode the URL-encoded client name
        return decodeURIComponent(clientName.replace(/\+/g, ' '));
      } catch (e) {
        // If already decoded or invalid, return as is
        return clientName;
      }
    }
    const params = new URLSearchParams(location.search);
    const name = params.get('client_name') || params.get('client') || '';
    if (name) {
      try {
        return decodeURIComponent(name.replace(/\+/g, ' '));
      } catch (e) {
        return name;
      }
    }
    return '';
  };

  const fetchClientDetails = async () => {
    const name = getClientName();
    if (!name) {
      error('Client name is required');
      navigate('/clients');
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/transactions/client-details/${encodeURIComponent(name)}`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        // Ensure client_name is properly decoded if it comes encoded from API
        if (data.client_name) {
          try {
            data.client_name = decodeURIComponent(data.client_name);
          } catch (e) {
            // Already decoded or invalid, use as is
          }
        }
        setClientDetails(data);
        logger.info('Client details loaded:', data.client_name);
      } else {
        error('Failed to load client details');
        navigate('/clients');
      }
    } catch (err: any) {
      logger.error('Error fetching client details:', err);
      error(err.message || 'Failed to load client details');
      navigate('/clients');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      fetchClientDetails();
    }
  }, [isAuthenticated, authLoading, clientName, location.search]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-300 border-t-gray-900 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading client details...</p>
        </div>
      </div>
    );
  }

  if (!clientDetails) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Client not found</p>
          <UnifiedButton onClick={() => navigate('/clients')} icon={<ArrowLeft className="w-4 h-4" />}>
            Back to Clients
          </UnifiedButton>
        </div>
      </div>
    );
  }

  const { statistics, metadata, transactions } = clientDetails;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <Breadcrumb
            items={[
              { label: t('navigation.dashboard'), href: '/dashboard' },
              { label: t('navigation.clients'), href: '/clients' },
              { label: clientDetails.client_name }
            ]}
          />
          
          <div className="mt-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <UnifiedButton
                variant="ghost"
                size="sm"
                onClick={() => navigate('/clients')}
                icon={<ArrowLeft className="w-4 h-4" />}
                className="text-gray-700 hover:text-gray-900"
              >
                Back
              </UnifiedButton>
              <div>
                <h1 className="text-2xl font-semibold text-gray-900 flex items-center gap-2">
                  {clientDetails.client_name}
                </h1>
                {clientDetails.company_name && (
                  <p className="text-sm text-gray-600 mt-1">{clientDetails.company_name}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={fetchClientDetails}
                icon={<RefreshCw className="w-4 h-4" />}
                className="text-gray-700 border-gray-300 hover:bg-gray-50"
              >
                Refresh
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => navigate(`/clients?client_name=${encodeURIComponent(clientDetails.client_name)}&tab=clients`)}
                icon={<Edit className="w-4 h-4" />}
                className="text-gray-700 border-gray-300 hover:bg-gray-50"
              >
                Edit
              </UnifiedButton>
            </div>
          </div>
        </div>

        {/* Statistics Cards */}
        <UnifiedGrid cols={4} gap="md" className="mb-6">
          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Total Volume</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(statistics.total_amount, 'TRY')}
              </p>
            </div>
          </UnifiedCard>

          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Total Commission</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(statistics.total_commission, 'TRY')}
              </p>
            </div>
          </UnifiedCard>

          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Net Amount</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(statistics.total_net, 'TRY')}
              </p>
            </div>
          </UnifiedCard>

          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Transactions</p>
              <p className="text-2xl font-semibold text-gray-900">
                {statistics.transaction_count}
              </p>
            </div>
          </UnifiedCard>
        </UnifiedGrid>

        {/* Additional Statistics */}
        <UnifiedGrid cols={3} gap="md" className="mb-6">
          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Total Deposits</p>
              <p className="text-xl font-semibold text-gray-900">
                {formatCurrency(statistics.total_deposits, 'TRY')}
              </p>
            </div>
          </UnifiedCard>

          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Total Withdrawals</p>
              <p className="text-xl font-semibold text-gray-900">
                {formatCurrency(statistics.total_withdrawals, 'TRY')}
              </p>
            </div>
          </UnifiedCard>

          <UnifiedCard variant="flat" className="border border-gray-200">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Average Transaction</p>
              <p className="text-xl font-semibold text-gray-900">
                {formatCurrency(statistics.avg_transaction, 'TRY')}
              </p>
            </div>
          </UnifiedCard>
        </UnifiedGrid>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-white border-b border-gray-200 rounded-none h-auto p-0">
            <TabsTrigger 
              value="overview"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-gray-900 data-[state=active]:bg-transparent data-[state=active]:text-gray-900 py-3 px-4"
            >
              Overview
            </TabsTrigger>
            <TabsTrigger 
              value="transactions"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-gray-900 data-[state=active]:bg-transparent data-[state=active]:text-gray-900 py-3 px-4"
            >
              Transactions ({transactions.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <UnifiedGrid cols={2} gap="md">
              {/* Metadata */}
              <UnifiedCard
                variant="flat"
                className="border border-gray-200"
                header={{
                  title: 'Client Information',
                  description: 'Payment methods, currencies, and providers'
                }}
              >
                <div className="space-y-5">
                  {metadata.currencies.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Currencies</p>
                      <div className="flex flex-wrap gap-2">
                        {metadata.currencies.map((currency) => (
                          <UnifiedBadge key={currency} variant="outline" className="bg-white border-gray-300 text-gray-700">
                            {currency}
                          </UnifiedBadge>
                        ))}
                      </div>
                    </div>
                  )}

                  {metadata.payment_methods.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Payment Methods</p>
                      <div className="flex flex-wrap gap-2">
                        {metadata.payment_methods.map((method) => (
                          <UnifiedBadge key={method} variant="outline" className="bg-white border-gray-300 text-gray-700">
                            {method}
                          </UnifiedBadge>
                        ))}
                      </div>
                    </div>
                  )}

                  {metadata.psps.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Payment Service Providers</p>
                      <div className="flex flex-wrap gap-2">
                        {metadata.psps.map((psp) => (
                          <UnifiedBadge key={psp} variant="outline" className="bg-white border-gray-300 text-gray-700">
                            {psp}
                          </UnifiedBadge>
                        ))}
                      </div>
                    </div>
                  )}

                  {metadata.categories.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Categories</p>
                      <div className="flex flex-wrap gap-2">
                        {metadata.categories.map((category) => (
                          <UnifiedBadge key={category} variant="outline" className="bg-white border-gray-300 text-gray-700">
                            {category}
                          </UnifiedBadge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </UnifiedCard>

              {/* Timeline */}
              <UnifiedCard
                variant="flat"
                className="border border-gray-200"
                header={{
                  title: 'Transaction Timeline',
                  description: 'First and last transaction dates'
                }}
              >
                <div className="space-y-4">
                  <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">First Transaction</p>
                      <p className="text-base font-semibold text-gray-900">
                        {statistics.first_transaction 
                          ? new Date(statistics.first_transaction).toLocaleDateString()
                          : 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Last Transaction</p>
                      <p className="text-base font-semibold text-gray-900">
                        {statistics.last_transaction 
                          ? new Date(statistics.last_transaction).toLocaleDateString()
                          : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              </UnifiedCard>
            </UnifiedGrid>
          </TabsContent>

          <TabsContent value="transactions" className="mt-6">
            <UnifiedCard variant="flat" className="border border-gray-200">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Date</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Category</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Payment Method</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">PSP</th>
                      <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Amount</th>
                      <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Commission</th>
                      <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Net Amount</th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wide">Currency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="py-3 px-4 text-sm text-gray-900">
                          {tx.date ? new Date(tx.date).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="py-3 px-4">
                          <UnifiedBadge variant="outline" size="sm" className="bg-white border-gray-300 text-gray-700">
                            {tx.category || 'N/A'}
                          </UnifiedBadge>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-700">{tx.payment_method || 'N/A'}</td>
                        <td className="py-3 px-4 text-sm text-gray-700">{tx.psp || 'N/A'}</td>
                        <td className="py-3 px-4 text-sm text-right font-medium text-gray-900">
                          {formatCurrency(tx.amount, tx.currency || 'TRY')}
                        </td>
                        <td className="py-3 px-4 text-sm text-right font-medium text-gray-900">
                          {formatCurrency(tx.commission, tx.currency || 'TRY')}
                        </td>
                        <td className="py-3 px-4 text-sm text-right font-semibold text-gray-900">
                          {formatCurrency(tx.net_amount, tx.currency || 'TRY')}
                        </td>
                        <td className="py-3 px-4">
                          <UnifiedBadge variant="outline" size="sm" className="bg-white border-gray-300 text-gray-700">
                            {tx.currency || 'TRY'}
                          </UnifiedBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </UnifiedCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

