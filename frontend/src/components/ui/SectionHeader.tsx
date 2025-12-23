import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  actions?: React.ReactNode;
  badge?: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showDivider?: boolean;
}

/**
 * Unified Section Header Component
 * 
 * Features:
 * - Consistent styling across all pages
 * - Optional icon, badge, and actions
 * - Three sizes (sm, md, lg)
 * - Optional bottom divider
 * - Minimal, professional design
 * 
 * Usage:
 * <SectionHeader 
 *   title="Performance Metrics"
 *   description="Track your key performance indicators"
 *   icon={BarChart3}
 *   actions={<Button>Action</Button>}
 * />
 */
export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  description,
  icon: Icon,
  actions,
  badge,
  className = '',
  size = 'md',
  showDivider = false
}) => {
  const sizeConfig = {
    sm: {
      title: 'text-lg font-semibold',
      description: 'text-sm',
      icon: 'w-5 h-5',
      spacing: 'gap-2'
    },
    md: {
      title: 'text-xl font-bold',
      description: 'text-base',
      icon: 'w-6 h-6',
      spacing: 'gap-3'
    },
    lg: {
      title: 'text-2xl font-bold',
      description: 'text-lg',
      icon: 'w-7 h-7',
      spacing: 'gap-4'
    }
  };

  const config = sizeConfig[size];

  return (
    <div className={`${className}`}>
      <div className="flex items-center justify-between">
        <div className={`flex items-center ${config.spacing}`}>
          {Icon && (
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                <Icon className={`${config.icon} text-slate-700`} />
              </div>
            </div>
          )}
          
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className={`${config.title} text-slate-900 tracking-tight`}>
                {title}
              </h2>
              {badge}
            </div>
            {description && (
              <p className={`${config.description} text-slate-600 font-medium`}>
                {description}
              </p>
            )}
          </div>
        </div>

        {actions && (
          <div className="flex items-center gap-3">
            {actions}
          </div>
        )}
      </div>

      {showDivider && (
        <div className="mt-4 border-b border-slate-200" />
      )}
    </div>
  );
};

/**
 * Minimal Section Header - Ultra-clean variant
 */
export const MinimalSectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  description,
  actions,
  className = ''
}) => {
  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-slate-900">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-slate-600">
            {description}
          </p>
        )}
      </div>
      
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
};

export default SectionHeader;

