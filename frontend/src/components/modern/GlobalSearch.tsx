import React, { useState, useEffect } from 'react';
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

interface SearchResult {
  id: string;
  type: 'transaction' | 'client' | 'user' | 'report';
  title: string;
  description: string;
  value?: string;
  date?: string;
  status?: string;
}

interface GlobalSearchProps {
  onResultClick?: (result: SearchResult) => void;
}

export const GlobalSearch: React.FC<GlobalSearchProps> = ({ onResultClick }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  // Mock search data
  const mockData: SearchResult[] = [
    {
      id: '1',
      type: 'transaction',
      title: 'TXN-001 - Acme Corp',
      description: 'Payment processing transaction',
      value: '$12,500',
      date: '2024-01-15',
      status: 'completed'
    },
    {
      id: '2',
      type: 'client',
      title: 'Acme Corporation',
      description: 'Enterprise client with 45 transactions',
      value: '$125,000',
      date: '2024-01-10'
    },
    {
      id: '3',
      type: 'transaction',
      title: 'TXN-002 - Tech Solutions',
      description: 'Monthly subscription payment',
      value: '$8,500',
      date: '2024-01-14',
      status: 'pending'
    },
    {
      id: '4',
      type: 'client',
      title: 'Tech Solutions Inc',
      description: 'SME client with 12 transactions',
      value: '$45,000',
      date: '2024-01-08'
    },
    {
      id: '5',
      type: 'report',
      title: 'Monthly Revenue Report',
      description: 'January 2024 revenue analysis',
      value: '$456,730',
      date: '2024-01-01'
    }
  ];

  useEffect(() => {
    if (searchTerm.length > 2) {
      setLoading(true);
      // Simulate search delay
      setTimeout(() => {
        const filtered = mockData.filter(item =>
          item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.description.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setResults(filtered);
        setLoading(false);
      }, 300);
    } else {
      setResults([]);
    }
  }, [searchTerm]);

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
                      <div className="flex items-center gap-2">
                        {result.date && (
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            {new Date(result.date).toLocaleDateString()}
                          </div>
                        )}
                        {getStatusBadge(result.status)}
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted-foreground" />
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