import React from 'react';
import { Card, CardContent } from './card';

interface MobileTableProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Mobile-responsive table wrapper
 * Shows table on all screen sizes with horizontal scroll on mobile
 */
export const MobileTable: React.FC<MobileTableProps> = ({ 
  children, 
  className = '' 
}) => {
  return (
    <div className={`overflow-x-auto ${className}`}>
      {children}
    </div>
  );
};

/**
 * Mobile Card Row Component
 * Converts table rows to cards on mobile
 */
interface MobileCardRowProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const MobileCardRow: React.FC<MobileCardRowProps> = ({
  children,
  onClick,
  className = '',
}) => {
  return (
    <Card 
      className={`cursor-pointer hover:shadow-md transition-shadow ${className}`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        {children}
      </CardContent>
    </Card>
  );
};

