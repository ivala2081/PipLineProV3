/**
 * Breadcrumb Navigation Component
 * Provides consistent breadcrumb navigation across all pages
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useNavigation } from '../../contexts/NavigationContext';
import { ChevronRight, Home } from 'lucide-react';
import { clsx } from 'clsx';

interface BreadcrumbNavigationProps {
  className?: string;
  showHome?: boolean;
}

export const BreadcrumbNavigation: React.FC<BreadcrumbNavigationProps> = ({ 
  className = '',
  showHome = true 
}) => {
  const { state } = useNavigation();
  const { breadcrumbs } = state;

  if (breadcrumbs.length <= 1) {
    return null; // Don't show breadcrumbs for single-level pages
  }

  return (
    <nav 
      className={clsx('flex items-center space-x-1 text-sm text-gray-500', className)}
      aria-label="Breadcrumb"
    >
      {showHome && (
        <>
          <Link
            to="/dashboard"
            className="flex items-center hover:text-gray-700 transition-colors"
            aria-label="Go to dashboard"
          >
            <Home className="w-4 h-4" />
          </Link>
          <ChevronRight className="w-4 h-4 mx-1" />
        </>
      )}
      
      {breadcrumbs.map((item, index) => (
        <React.Fragment key={item.href}>
          {item.current ? (
            <span 
              className="font-medium text-gray-900"
              aria-current="page"
            >
              {item.label}
            </span>
          ) : (
            <Link
              to={item.href}
              className="hover:text-gray-700 transition-colors"
            >
              {item.label}
            </Link>
          )}
          
          {index < breadcrumbs.length - 1 && (
            <ChevronRight className="w-4 h-4 mx-1" />
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default BreadcrumbNavigation;
