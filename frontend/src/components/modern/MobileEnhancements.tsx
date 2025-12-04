import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  Menu, 
  X, 
  Search, 
  Bell, 
  User, 
  Settings,
  ChevronDown,
  ChevronUp,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

interface MobileEnhancementsProps {
  children: React.ReactNode;
}

export const MobileEnhancements: React.FC<MobileEnhancementsProps> = ({ children }) => {
  const [isMobile, setIsMobile] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState<'up' | 'down' | null>(null);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientY);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isUpSwipe = distance > 50;
    const isDownSwipe = distance < -50;

    if (isUpSwipe) {
      setSwipeDirection('up');
      // Handle swipe up action (e.g., show more content)
    } else if (isDownSwipe) {
      setSwipeDirection('down');
      // Handle swipe down action (e.g., refresh)
    }

    setTouchStart(null);
    setTouchEnd(null);
  };

  if (!isMobile) {
    return <>{children}</>;
  }

  return (
    <div 
      className="mobile-enhanced"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Mobile-specific enhancements */}
      <div className="lg:hidden">
        {/* Swipe indicator */}
        {swipeDirection && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
            <Card className="px-4 py-2">
              <div className="flex items-center gap-2 text-sm">
                {swipeDirection === 'up' ? (
                  <>
                    <ArrowUp className="w-4 h-4 text-primary" />
                    <span>Pull to refresh</span>
                  </>
                ) : (
                  <>
                    <ArrowDown className="w-4 h-4 text-primary" />
                    <span>Pull down for more</span>
                  </>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Mobile floating action button */}
        <div className="fixed bottom-6 right-6 z-40">
          <Button
            size="lg"
            className="rounded-full w-14 h-14 shadow-lg"
            onClick={() => {
              // Handle FAB action
              console.log('FAB clicked');
            }}
          >
            <Search className="w-6 h-6" />
          </Button>
        </div>

        {/* Mobile bottom navigation hint */}
        <div className="fixed bottom-0 left-0 right-0 bg-background border-t border-border p-2 lg:hidden">
          <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
            <div className="w-2 h-2 bg-primary rounded-full"></div>
            <span>Swipe up for more options</span>
          </div>
        </div>
      </div>

      {children}
    </div>
  );
};

// Mobile-optimized card component
export const MobileCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}> = ({ children, className = '', onClick }) => {
  return (
    <Card 
      className={`mobile-card ${className} ${onClick ? 'cursor-pointer active:scale-95 transition-transform' : ''}`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        {children}
      </CardContent>
    </Card>
  );
};

// Mobile-optimized button group
export const MobileButtonGroup: React.FC<{
  buttons: Array<{
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
    active?: boolean;
  }>;
  className?: string;
}> = ({ buttons, className = '' }) => {
  return (
    <div className={`flex gap-2 overflow-x-auto pb-2 ${className}`}>
      {buttons.map((button, index) => (
        <Button
          key={index}
          variant={button.active ? 'default' : button.variant || 'outline'}
          size="sm"
          onClick={button.onClick}
          className="flex-shrink-0 whitespace-nowrap"
        >
          {button.icon && <span className="mr-2">{button.icon}</span>}
          {button.label}
        </Button>
      ))}
    </div>
  );
};

// Mobile-optimized stats grid
export const MobileStatsGrid: React.FC<{
  stats: Array<{
    label: string;
    value: string;
    change?: string;
    trend?: 'up' | 'down' | 'neutral';
    icon?: React.ReactNode;
  }>;
}> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 gap-3">
      {stats.map((stat, index) => (
        <MobileCard key={index} className="text-center">
          <div className="space-y-2">
            {stat.icon && (
              <div className="flex justify-center">
                {stat.icon}
              </div>
            )}
            <div className="text-2xl font-bold text-foreground">
              {stat.value}
            </div>
            <div className="text-sm text-muted-foreground">
              {stat.label}
            </div>
            {stat.change && (
              <div className="flex items-center justify-center gap-1">
                {stat.trend === 'up' && <ChevronUp className="w-3 h-3 text-green-500" />}
                {stat.trend === 'down' && <ChevronDown className="w-3 h-3 text-red-500" />}
                <span className={`text-xs ${
                  stat.trend === 'up' ? 'text-green-500' : 
                  stat.trend === 'down' ? 'text-red-500' : 
                  'text-muted-foreground'
                }`}>
                  {stat.change}
                </span>
              </div>
            )}
          </div>
        </MobileCard>
      ))}
    </div>
  );
};

// Mobile-optimized list
export const MobileList: React.FC<{
  items: Array<{
    id: string;
    title: string;
    subtitle?: string;
    value?: string;
    status?: string;
    icon?: React.ReactNode;
    onClick?: () => void;
  }>;
  className?: string;
}> = ({ items, className = '' }) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {items.map((item) => (
        <MobileCard 
          key={item.id} 
          onClick={item.onClick}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            {item.icon && (
              <div className="flex-shrink-0">
                {item.icon}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="font-medium text-foreground truncate">
                {item.title}
              </div>
              {item.subtitle && (
                <div className="text-sm text-muted-foreground truncate">
                  {item.subtitle}
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {item.value && (
              <div className="text-sm font-medium text-foreground">
                {item.value}
              </div>
            )}
            {item.status && (
              <Badge variant="outline" className="text-xs">
                {item.status}
              </Badge>
            )}
          </div>
        </MobileCard>
      ))}
    </div>
  );
};
