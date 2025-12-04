/**
 * Navigation Loading Indicator
 * Shows loading state during navigation transitions
 */

import React from 'react';
import { useNavigation } from '../contexts/NavigationContext';
import { Loader2 } from 'lucide-react';

const NavigationLoadingIndicator: React.FC = () => {
  const { isNavigating, loadingMessage } = useNavigation();

  if (!isNavigating) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-sm border-b border-slate-200">
      <div className="flex items-center justify-center py-3 px-4">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <span className="text-sm font-medium text-slate-700">
            {loadingMessage}
          </span>
        </div>
      </div>
    </div>
  );
};

export default NavigationLoadingIndicator;
