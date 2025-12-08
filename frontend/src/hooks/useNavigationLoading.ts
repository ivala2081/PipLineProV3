/**
 * Navigation Loading Hook
 * Provides loading state management for navigation transitions
 */

import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export const useNavigationLoading = () => {
  const [isNavigating, setIsNavigating] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const location = useLocation();

  useEffect(() => {
    // Set loading state when location changes
    setIsNavigating(true);
    setLoadingMessage('Loading...');

    // Clear loading state after a short delay to allow for smooth transitions
    const timer = setTimeout(() => {
      setIsNavigating(false);
      setLoadingMessage('');
    }, 300);

    return () => clearTimeout(timer);
  }, [location.pathname]);

  const setLoading = (loading: boolean, message: string = 'Loading...') => {
    setIsNavigating(loading);
    setLoadingMessage(message);
  };

  return {
    isNavigating,
    loadingMessage,
    setLoading
  };
};

export default useNavigationLoading;
