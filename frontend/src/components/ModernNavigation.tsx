import React, { useState } from 'react';
import { LucideIcon, ChevronRight, Search, Bell, User, Settings } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: LucideIcon;
}

interface ModernBreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

interface QuickSearchProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
  suggestions?: string[];
  className?: string;
}

interface NotificationBadgeProps {
  count: number;
  variant?: 'default' | 'danger' | 'warning';
  size?: 'sm' | 'md';
}

interface UserMenuProps {
  user: {
    name: string;
    email: string;
    avatar?: string;
    role?: string;
  };
  menuItems?: Array<{
    label: string;
    icon?: LucideIcon;
    onClick: () => void;
    divider?: boolean;
  }>;
}

// Modern Breadcrumbs with Icons and Hover Effects
export const ModernBreadcrumbs: React.FC<ModernBreadcrumbsProps> = ({
  items,
  className = ''
}) => {
  return (
    <nav className={`flex items-center space-x-2 text-sm ${className}`}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const Icon = item.icon;
        
        return (
          <div key={index} className="flex items-center space-x-2">
            {item.href && !isLast ? (
              <a
                href={item.href}
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-gray-600 hover:text-gray-600 hover:bg-gray-50 transition-all duration-200"
              >
                {Icon && <Icon className="h-4 w-4" />}
                <span>{item.label}</span>
              </a>
            ) : (
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${
                isLast 
                  ? 'text-gray-900 font-medium bg-gray-100' 
                  : 'text-gray-600'
              }`}>
                {Icon && <Icon className="h-4 w-4" />}
                <span>{item.label}</span>
              </div>
            )}
            
            {!isLast && (
              <ChevronRight className="h-4 w-4 text-gray-400" />
            )}
          </div>
        );
      })}
    </nav>
  );
};

// Enhanced Quick Search with Suggestions
export const QuickSearch: React.FC<QuickSearchProps> = ({
  placeholder = "Search...",
  onSearch,
  suggestions = [],
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);

  const handleInputChange = (value: string) => {
    setQuery(value);
    
    if (value.length > 0) {
      const filtered = suggestions.filter(suggestion =>
        suggestion.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredSuggestions(filtered);
      setIsOpen(filtered.length > 0);
    } else {
      setIsOpen(false);
    }
  };

  const handleSearch = (searchQuery: string) => {
    onSearch?.(searchQuery);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch(query)}
          placeholder={placeholder}
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-white focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all duration-200 placeholder-gray-400"
        />
      </div>
      
      {isOpen && filteredSuggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 max-h-60 overflow-y-auto">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSearch(suggestion)}
              className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none first:rounded-t-xl last:rounded-b-xl"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Notification Badge with Animation
export const NotificationBadge: React.FC<NotificationBadgeProps> = ({
  count,
  variant = 'default',
  size = 'md'
}) => {
  if (count === 0) return null;

  const variantClasses = {
    default: 'bg-gray-500 text-white',
    danger: 'bg-red-500 text-white',
    warning: 'bg-amber-500 text-white'
  };

  const sizeClasses = {
    sm: 'h-4 w-4 text-xs',
    md: 'h-5 w-5 text-xs'
  };

  const displayCount = count > 99 ? '99+' : count.toString();

  return (
    <div className={`
      ${variantClasses[variant]}
      ${sizeClasses[size]}
      rounded-full
      flex
      items-center
      justify-center
      font-medium
      animate-pulse
      shadow-sm
      border-2
      border-white
    `}>
      {displayCount}
    </div>
  );
};

// Modern User Menu with Avatar
export const UserMenu: React.FC<UserMenuProps> = ({
  user,
  menuItems = []
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const defaultMenuItems = [
    {
      label: 'Profile Settings',
      icon: User,
      onClick: () => console.log('Profile clicked')
    },
    {
      label: 'Account Settings',
      icon: Settings,
      onClick: () => console.log('Settings clicked')
    },
    {
      label: 'Sign Out',
      onClick: () => console.log('Sign out clicked'),
      divider: true
    }
  ];

  const items = menuItems.length > 0 ? menuItems : defaultMenuItems;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
      >
        {/* Avatar */}
        <div className="relative">
          {user.avatar ? (
            <img
              src={user.avatar}
              alt={user.name}
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-gray-500 to-gray-600 flex items-center justify-center text-white text-sm font-medium">
              {user.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 bg-green-400 border-2 border-white rounded-full"></div>
        </div>
        
        {/* User Info */}
        <div className="hidden md:block text-left">
          <div className="text-sm font-medium text-gray-900">
            {user.name}
          </div>
          {user.role && (
            <div className="text-xs text-gray-500">
              {user.role}
            </div>
          )}
        </div>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-lg z-50">
          <div className="p-3 border-b border-gray-100">
            <div className="text-sm font-medium text-gray-900">
              {user.name}
            </div>
            <div className="text-xs text-gray-500">
              {user.email}
            </div>
          </div>
          
          <div className="py-2">
            {items.map((item, index) => (
              <div key={index}>
                {item.divider && (
                  <div className="border-t border-gray-100 my-2" />
                )}
                <button
                  onClick={() => {
                    item.onClick();
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none"
                >
                  {item.icon && <item.icon className="h-4 w-4" />}
                  {item.label}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default { ModernBreadcrumbs, QuickSearch, NotificationBadge, UserMenu };
