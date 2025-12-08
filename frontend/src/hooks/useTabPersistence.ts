import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * Custom hook for persisting tab state in URL parameters
 * 
 * When navigating to a page from sidebar (no URL params), always shows the default tab.
 * When user changes tabs, the selected tab is persisted in URL for sharing and bookmarking.
 * 
 * @param defaultTab - Default tab to show when navigating fresh from sidebar
 * @returns [activeTab, handleTabChange] - Current tab and handler to change tabs
 * 
 * @example
 * const [activeTab, handleTabChange] = useTabPersistence<'overview' | 'expenses'>('overview');
 */
export function useTabPersistence<T extends string>(
  defaultTab: T
): [T, (tab: string) => void] {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Get initial tab from URL params or default
  const getInitialTab = (): T => {
    // First priority: URL parameter (explicit navigation with tab)
    const tabFromUrl = searchParams.get('tab') as T;
    if (tabFromUrl) {
      return tabFromUrl;
    }
    
    // When navigating fresh from sidebar (no URL param), always show default tab
    // This ensures users see the first tab when clicking sidebar navigation
    return defaultTab;
  };
  
  const [activeTab, setActiveTab] = useState<T>(getInitialTab());
  
  // Handle tab change with URL persistence
  const handleTabChange = useCallback((value: string) => {
    const newTab = value as T;
    setActiveTab(newTab);
    
    // Update URL params while preserving other parameters
    const currentParams = new URLSearchParams(searchParams);
    currentParams.set('tab', newTab);
    setSearchParams(currentParams, { replace: true }); // Use replace to avoid cluttering browser history
  }, [searchParams, setSearchParams]);
  
  return [activeTab, handleTabChange];
}

