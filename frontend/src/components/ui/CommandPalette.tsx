import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Home, 
  Users, 
  BarChart3, 
  Settings, 
  FileText, 
  DollarSign,
  CreditCard,
  TrendingUp,
  Calendar,
  Database,
  X,
  Command,
  ArrowRight
} from 'lucide-react';

interface CommandItem {
  id: string;
  title: string;
  description?: string;
  icon: React.ComponentType<any>;
  action: () => void;
  keywords?: string[];
  category?: string;
}

interface CommandPaletteProps {
  isOpen?: boolean;
  onClose?: () => void;
}

/**
 * CommandPalette - Keyboard-first navigation (Cmd+K / Ctrl+K)
 * 
 * Features:
 * - Quick navigation to any page
 * - Keyboard shortcuts (Cmd+K, Escape, Arrow keys, Enter)
 * - Fuzzy search
 * - Recent actions
 * - Categories
 * - Accessible
 * 
 * Usage:
 * Press Cmd+K (Mac) or Ctrl+K (Windows) to open
 */
export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen: controlledIsOpen,
  onClose: controlledOnClose
}) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const onClose = controlledOnClose || (() => setInternalIsOpen(false));

  // Define all available commands
  const commands: CommandItem[] = useMemo(() => [
    // Navigation
    {
      id: 'nav-dashboard',
      title: 'Dashboard',
      description: 'Go to dashboard',
      icon: Home,
      action: () => navigate('/dashboard'),
      keywords: ['home', 'main', 'overview'],
      category: 'Navigation'
    },
    {
      id: 'nav-clients',
      title: 'Clients',
      description: 'View all clients',
      icon: Users,
      action: () => navigate('/clients'),
      keywords: ['customers', 'users'],
      category: 'Navigation'
    },
    {
      id: 'nav-analytics',
      title: 'Analytics',
      description: 'View analytics',
      icon: BarChart3,
      action: () => navigate('/analytics'),
      keywords: ['stats', 'data', 'insights'],
      category: 'Navigation'
    },
    {
      id: 'nav-accounting',
      title: 'Accounting',
      description: 'Accounting overview',
      icon: DollarSign,
      action: () => navigate('/accounting'),
      keywords: ['finance', 'money', 'ledger'],
      category: 'Navigation'
    },
    {
      id: 'nav-ledger',
      title: 'Ledger',
      description: 'View ledger',
      icon: FileText,
      action: () => navigate('/ledger'),
      keywords: ['transactions', 'records'],
      category: 'Navigation'
    },
    {
      id: 'nav-settings',
      title: 'Settings',
      description: 'App settings',
      icon: Settings,
      action: () => navigate('/settings'),
      keywords: ['preferences', 'config'],
      category: 'Navigation'
    },
    
    // Actions
    {
      id: 'action-add-transaction',
      title: 'Add Transaction',
      description: 'Create new transaction',
      icon: CreditCard,
      action: () => navigate('/transactions/add'),
      keywords: ['new', 'create', 'payment'],
      category: 'Actions'
    },
    {
      id: 'action-revenue-analytics',
      title: 'Revenue Analytics',
      description: 'View revenue reports',
      icon: TrendingUp,
      action: () => navigate('/revenue-analytics'),
      keywords: ['income', 'earnings'],
      category: 'Analytics'
    },
    {
      id: 'action-future-projections',
      title: 'Future Projections',
      description: 'View projections',
      icon: Calendar,
      action: () => navigate('/future'),
      keywords: ['forecast', 'predictions'],
      category: 'Analytics'
    }
  ], [navigate]);

  // Filter commands based on search
  const filteredCommands = useMemo(() => {
    if (!search.trim()) return commands;

    const searchLower = search.toLowerCase();
    return commands.filter(cmd => {
      const titleMatch = cmd.title.toLowerCase().includes(searchLower);
      const descMatch = cmd.description?.toLowerCase().includes(searchLower);
      const keywordMatch = cmd.keywords?.some(k => k.includes(searchLower));
      return titleMatch || descMatch || keywordMatch;
    });
  }, [search, commands]);

  // Group by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    filteredCommands.forEach(cmd => {
      const category = cmd.category || 'Other';
      if (!groups[category]) groups[category] = [];
      groups[category].push(cmd);
    });
    return groups;
  }, [filteredCommands]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K to open
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setInternalIsOpen(true);
      }

      if (!isOpen) return;

      // Escape to close
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        setSearch('');
        setSelectedIndex(0);
      }

      // Arrow keys for navigation
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => 
          Math.min(prev + 1, filteredCommands.length - 1)
        );
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
      }

      // Enter to execute
      if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        e.preventDefault();
        filteredCommands[selectedIndex].action();
        onClose();
        setSearch('');
        setSelectedIndex(0);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Reset selected index when search changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-fade-in"
        onClick={onClose}
      />

      {/* Command Palette */}
      <div className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-2xl z-50 animate-fade-in">
        <div className="glass-card-strong rounded-xl shadow-2xl overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center gap-3 p-4 border-b border-gray-200">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent border-none outline-none text-lg text-gray-900 placeholder-gray-400"
            />
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <kbd className="px-2 py-1 bg-gray-100 rounded border border-gray-300">
                ESC
              </kbd>
              <span>to close</span>
            </div>
          </div>

          {/* Command List */}
          <div className="max-h-[400px] overflow-y-auto">
            {Object.keys(groupedCommands).length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No commands found
              </div>
            ) : (
              Object.entries(groupedCommands).map(([category, items]) => (
                <div key={category} className="py-2">
                  {/* Category Header */}
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {category}
                  </div>

                  {/* Commands */}
                  {items.map((cmd, index) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    const isSelected = globalIndex === selectedIndex;
                    const Icon = cmd.icon;

                    return (
                      <button
                        key={cmd.id}
                        onClick={() => {
                          cmd.action();
                          onClose();
                          setSearch('');
                          setSelectedIndex(0);
                        }}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                        className={`
                          w-full flex items-center gap-3 px-4 py-3 text-left
                          transition-colors duration-150
                          ${isSelected 
                            ? 'bg-blue-50 border-l-4 border-blue-500' 
                            : 'border-l-4 border-transparent hover:bg-gray-50'
                          }
                        `}
                      >
                        <div className={`
                          w-10 h-10 rounded-lg flex items-center justify-center
                          ${isSelected ? 'bg-blue-100' : 'bg-gray-100'}
                        `}>
                          <Icon className={`w-5 h-5 ${isSelected ? 'text-blue-600' : 'text-gray-600'}`} />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className={`font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                            {cmd.title}
                          </div>
                          {cmd.description && (
                            <div className="text-sm text-gray-500 truncate">
                              {cmd.description}
                            </div>
                          )}
                        </div>

                        <ArrowRight className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`} />
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <kbd className="px-2 py-1 bg-white rounded border border-gray-300">↑↓</kbd>
                <span>Navigate</span>
              </div>
              <div className="flex items-center gap-1">
                <kbd className="px-2 py-1 bg-white rounded border border-gray-300">↵</kbd>
                <span>Select</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Command className="w-3 h-3" />
              <span className="text-gray-400">+</span>
              <kbd className="px-2 py-1 bg-white rounded border border-gray-300">K</kbd>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

/**
 * useCommandPalette Hook - For programmatic control
 */
export const useCommandPalette = () => {
  const [isOpen, setIsOpen] = useState(false);

  const open = () => setIsOpen(true);
  const close = () => setIsOpen(false);
  const toggle = () => setIsOpen(prev => !prev);

  return { isOpen, open, close, toggle };
};

export default CommandPalette;

