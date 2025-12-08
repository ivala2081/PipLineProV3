/**
 * Professional Accessibility Context
 * Provides accessibility features without overwhelming the UI
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AccessibilitySettings {
  highContrast: boolean;
  reducedMotion: boolean;
  focusVisible: boolean;
  fontSize: 'small' | 'medium' | 'large';
  keyboardNavigation: boolean;
}

interface AccessibilityContextType {
  settings: AccessibilitySettings;
  updateSettings: (settings: Partial<AccessibilitySettings>) => void;
  resetSettings: () => void;
  isHighContrast: boolean;
  isReducedMotion: boolean;
  isFocusVisible: boolean;
  fontSize: string;
  isKeyboardNavigation: boolean;
}

const defaultSettings: AccessibilitySettings = {
  highContrast: false,
  reducedMotion: false,
  focusVisible: true,
  fontSize: 'medium',
  keyboardNavigation: true,
};

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

interface AccessibilityProviderProps {
  children: ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    // Load from localStorage or use defaults
    try {
      const saved = localStorage.getItem('accessibility-settings');
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    } catch {
      return defaultSettings;
    }
  });

  // Apply settings to document
  useEffect(() => {
    const root = document.documentElement;
    
    // Apply high contrast
    if (settings.highContrast) {
      root.classList.add('contrast-enhanced');
    } else {
      root.classList.remove('contrast-enhanced');
    }
    
    // Apply reduced motion
    if (settings.reducedMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }
    
    // Apply focus visible
    if (settings.focusVisible) {
      root.classList.add('focus-visible-enabled');
    } else {
      root.classList.remove('focus-visible-enabled');
    }
    
    // Apply keyboard navigation
    if (settings.keyboardNavigation) {
      root.classList.add('keyboard-navigation');
    } else {
      root.classList.remove('keyboard-navigation');
    }
    
    // Apply font size
    root.style.setProperty('--user-font-size', getFontSizeValue(settings.fontSize));
    
    // Save to localStorage
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));
    
  }, [settings]);

  // Listen for system preferences
  useEffect(() => {
    const mediaQueries = {
      prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)'),
      prefersHighContrast: window.matchMedia('(prefers-contrast: high)'),
    };

    const handleChange = () => {
      setSettings(prev => ({
        ...prev,
        reducedMotion: mediaQueries.prefersReducedMotion.matches,
        highContrast: mediaQueries.prefersHighContrast.matches,
      }));
    };

    // Set initial values
    handleChange();

    // Listen for changes
    mediaQueries.prefersReducedMotion.addEventListener('change', handleChange);
    mediaQueries.prefersHighContrast.addEventListener('change', handleChange);

    return () => {
      mediaQueries.prefersReducedMotion.removeEventListener('change', handleChange);
      mediaQueries.prefersHighContrast.removeEventListener('change', handleChange);
    };
  }, []);

  const updateSettings = (newSettings: Partial<AccessibilitySettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
  };

  const getFontSizeValue = (size: string): string => {
    switch (size) {
      case 'small': return '0.875rem';
      case 'large': return '1.125rem';
      default: return '1rem';
    }
  };

  const value: AccessibilityContextType = {
    settings,
    updateSettings,
    resetSettings,
    isHighContrast: settings.highContrast,
    isReducedMotion: settings.reducedMotion,
    isFocusVisible: settings.focusVisible,
    fontSize: getFontSizeValue(settings.fontSize),
    isKeyboardNavigation: settings.keyboardNavigation,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = (): AccessibilityContextType => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};

// Export the context for external use if needed
export { AccessibilityContext };

// Utility hook for keyboard navigation
export const useKeyboardNavigation = () => {
  const { isKeyboardNavigation } = useAccessibility();
  const [isKeyboardUser, setIsKeyboardUser] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        setIsKeyboardUser(true);
      }
    };

    const handleMouseDown = () => {
      setIsKeyboardUser(false);
    };

    if (isKeyboardNavigation) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleMouseDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, [isKeyboardNavigation]);

  return {
    isKeyboardUser,
    isKeyboardNavigation,
    focusVisible: isKeyboardNavigation && isKeyboardUser,
  };
};

// Utility hook for focus management
export const useFocusManagement = () => {
  const { isFocusVisible } = useAccessibility();

  const focusElement = (element: HTMLElement | null) => {
    if (element && isFocusVisible) {
      element.focus();
    }
  };

  const trapFocus = (container: HTMLElement | null) => {
    if (!container || !isFocusVisible) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            event.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            event.preventDefault();
          }
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  };

  return {
    focusElement,
    trapFocus,
    isFocusVisible,
  };
};

// Utility hook for screen reader announcements
export const useScreenReader = () => {
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  };

  return { announce };
};

// Removed default export to fix HMR compatibility
