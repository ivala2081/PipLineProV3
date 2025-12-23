import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  Search, 
  X, 
  FileText, 
  Users, 
  DollarSign, 
  Building2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { api } from '../../utils/apiClient';
import { formatCurrency } from '../../utils/currencyUtils';

interface SearchResult {
  id: string;
  type: 'transaction' | 'client' | 'user' | 'report';
  title: string;
  description: string;
  value?: string;
  date?: string;
  status?: string;
  clientData?: any;
}

interface GlobalSearchProps {
  onResultClick?: (result: SearchResult) => void;
}

export const GlobalSearch: React.FC<GlobalSearchProps> = ({ onResultClick }) => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const searchClients = useCallback(async (term: string) => {
    if (term.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/transactions/search-clients?q=${encodeURIComponent(term)}`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        
        const searchResults: SearchResult[] = [];
        
        // Add client results
        if (data.clients && Array.isArray(data.clients)) {
          data.clients.forEach((client: any) => {
            searchResults.push({
              id: `client-${client.client_name}`,
              type: 'client',
              title: client.client_name,
              description: `${client.transaction_count} transaction${client.transaction_count !== 1 ? 's' : ''} • Total: ${formatCurrency(client.total_amount, 'TRY')}`,
              value: formatCurrency(client.total_amount, 'TRY'),
              date: client.last_transaction || client.first_transaction,
              clientData: client
            });
          });
        }
        
        // Add recent transactions
        if (data.transactions && Array.isArray(data.transactions)) {
          data.transactions.slice(0, 5).forEach((tx: any) => {
            searchResults.push({
              id: `tx-${tx.id}`,
              type: 'transaction',
              title: `${tx.client_name} - ${tx.category || 'Transaction'}`,
              description: `${tx.payment_method || ''} • ${tx.psp || ''}`,
              value: formatCurrency(tx.amount, tx.currency || 'TRY'),
              date: tx.date,
              status: 'completed'
            });
          });
        }
        
        setResults(searchResults);
      } else {
        setResults([]);
      }
    } catch (error) {
      console.error('Error searching clients:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchClients(searchTerm);
    }, 300); // Debounce search

    return () => clearTimeout(timeoutId);
  }, [searchTerm, searchClients]);

  // Close search dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && !(event.target as Element).closest('.search-container')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'transaction': return <DollarSign className="w-4 h-4" />;
      case 'client': return <Building2 className="w-4 h-4" />;
      case 'user': return <Users className="w-4 h-4" />;
      case 'report': return <FileText className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return null;
    
    const statusConfig = {
      completed: { variant: 'default' as const, color: 'bg-green-100 text-green-800' },
      pending: { variant: 'secondary' as const, color: 'bg-yellow-100 text-yellow-800' },
      processing: { variant: 'outline' as const, color: 'bg-gray-100 text-gray-800' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <Badge variant={config.variant} className={config.color}>
        {status}
      </Badge>
    );
  };

  const handleResultClick = (result: SearchResult) => {
    if (result.type === 'client' && result.clientData) {
      // Navigate to dedicated client detail page
      navigate(`/clients/${encodeURIComponent(result.clientData.client_name)}`);
    } else if (result.type === 'transaction') {
      // Navigate to client detail page for the transaction's client
      const clientName = result.title.split(' - ')[0];
      navigate(`/clients/${encodeURIComponent(clientName)}`);
    }
    
    onResultClick?.(result);
    setIsOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="relative search-container">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
        <Input
          type="text"
          placeholder="Search transactions, clients, reports..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setIsOpen(true)}
          className="pl-10 pr-10 w-80"
        />
        {searchTerm && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchTerm('');
              setIsOpen(false);
            }}
            className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>

      {isOpen && (searchTerm.length > 2 || results.length > 0) && (
        <Card className="absolute top-full left-0 right-0 mt-2 z-50 max-h-96 overflow-y-auto">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-4 text-center text-muted-foreground">
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                Searching...
              </div>
            ) : results.length > 0 ? (
              <div className="py-2">
                {results.map((result) => (
                  <div
                    key={result.id}
                    onClick={() => handleResultClick(result)}
                    className="flex items-center gap-3 p-3 hover:bg-muted/50 cursor-pointer border-b border-border last:border-b-0"
                  >
                    <div className="flex-shrink-0">
                      {getResultIcon(result.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-medium text-foreground truncate">
                          {result.title}
                        </p>
                        {result.value && (
                          <span className="text-sm font-medium text-foreground">
                            {result.value}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mb-1">
                        {result.description}
                      </p>
                      {result.type === 'client' && result.clientData && (
                        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                          {result.clientData.transaction_count > 0 && (
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {result.clientData.transaction_count} transactions
                            </span>
                          )}
                          {result.clientData.total_commission > 0 && (
                            <span className="flex items-center gap-1">
                              <DollarSign className="w-3 h-3" />
                              Commission: {formatCurrency(result.clientData.total_commission, 'TRY')}
                            </span>
                          )}
                        </div>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        {result.date && (
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            {new Date(result.date).toLocaleDateString()}
                          </div>
                        )}
                        {getStatusBadge(result.status)}
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  </div>
                ))}
              </div>
            ) : searchTerm.length > 2 ? (
              <div className="p-4 text-center text-muted-foreground">
                <Search className="w-8 h-8 mx-auto mb-2 text-muted-foreground/50" />
                <p>No results found for "{searchTerm}"</p>
                <p className="text-xs mt-1">Try different keywords</p>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GlobalSearch;