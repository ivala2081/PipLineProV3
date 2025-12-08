/**
 * Scroll Restoration Hook
 * Automatically scrolls to top when route changes
 */

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export const useScrollRestoration = () => {
  const location = useLocation();

  useEffect(() => {
    // Scroll to top when route changes
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: 'smooth'
    });
  }, [location.pathname]);

  // Also scroll to top on initial load
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);
};

export default useScrollRestoration;
