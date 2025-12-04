import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { useAuth, AuthContext } from './AuthContext';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n/config';

// Supported languages (currently only EN and TR are fully translated)
export const SUPPORTED_LANGUAGES = {
  en: { name: 'English', flag: '' },
  tr: { name: 'Türkçe', flag: '' },
};

export type LanguageCode = keyof typeof SUPPORTED_LANGUAGES;

interface LanguageContextType {
  currentLanguage: LanguageCode;
  setLanguage: (language: LanguageCode) => Promise<void>;
  t: (key: string, params?: Record<string, string | number>) => string;
  isLoading: boolean;
  supportedLanguages: typeof SUPPORTED_LANGUAGES;
}

const LanguageContext = createContext<LanguageContextType | undefined>(
  undefined
);

interface LanguageProviderProps {
  children: ReactNode;
}

export function LanguageProvider({ children }: LanguageProviderProps) {
  // Initialize from localStorage if available, otherwise default to 'en'
  const [currentLanguage, setCurrentLanguage] = useState<LanguageCode>(() => {
    const savedLanguage = localStorage.getItem('pipline_language') || localStorage.getItem('preferred-language');
    if (savedLanguage && SUPPORTED_LANGUAGES[savedLanguage as LanguageCode]) {
      return savedLanguage as LanguageCode;
    }
    return 'en';
  });
  const [isLoading, setIsLoading] = useState(false);
  // CRITICAL FIX: Safely access auth context - may not be available during HMR
  // Use useContext directly to avoid throwing error during HMR
  // AuthContext will be undefined if not within AuthProvider, which is OK
  let user = null;
  try {
    const authContext = useContext(AuthContext);
    user = authContext?.user || null;
  } catch (error) {
    // Context not available - this is OK during initial render or HMR
    // Silently handle - don't log to avoid console spam
  }
  const { t: i18nT } = useTranslation();

  // Sync i18n language with context
  useEffect(() => {
    if (i18n.language !== currentLanguage) {
      i18n.changeLanguage(currentLanguage);
    }
  }, [currentLanguage]);

  // Load user's preferred language on mount (only once)
  useEffect(() => {
    const loadUserLanguage = async () => {
      // Priority 1: Check localStorage first for saved preference
      const savedLanguage = localStorage.getItem('pipline_language') || localStorage.getItem('preferred-language');
      if (savedLanguage && SUPPORTED_LANGUAGES[savedLanguage as LanguageCode]) {
        setCurrentLanguage(savedLanguage as LanguageCode);
        await i18n.changeLanguage(savedLanguage);
        console.log('[LanguageContext] Loaded language from localStorage:', savedLanguage);
        return;
      }

      // Priority 2: Try to load from backend if user is authenticated
      if (user) {
        try {
          const response = await fetch('/api/v1/users/settings', {
            method: 'GET',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          if (response.ok) {
            const data = await response.json();
            if (data.language && SUPPORTED_LANGUAGES[data.language as LanguageCode]) {
              setCurrentLanguage(data.language);
              await i18n.changeLanguage(data.language);
              // Save to localStorage for future sessions
              localStorage.setItem('pipline_language', data.language);
              console.log('[LanguageContext] Loaded language from backend:', data.language);
              return;
            }
          }
        } catch (error) {
          console.error('Failed to load user language:', error);
          // Continue to fallback options
        }
      }

      // Priority 3: Use browser language
      const browserLang = navigator.language.split('-')[0] as LanguageCode;
      if (SUPPORTED_LANGUAGES[browserLang]) {
        setCurrentLanguage(browserLang);
        await i18n.changeLanguage(browserLang);
        console.log('[LanguageContext] Using browser language:', browserLang);
      } else {
        // Priority 4: Default to English
        setCurrentLanguage('en');
        await i18n.changeLanguage('en');
        console.log('[LanguageContext] Using default language: en');
      }
    };

    loadUserLanguage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount, not when user changes

  // Translation function using i18next
  const t = (key: string, params?: Record<string, string | number>): string => {
    try {
      const result = i18nT(key, params as any);
      return typeof result === 'string' ? result : key;
    } catch (error) {
      console.error('Translation error:', error);
      return key;
    }
  };

  // Set language function
  const setLanguage = async (language: LanguageCode) => {
    if (!SUPPORTED_LANGUAGES[language]) {
      throw new Error(`Unsupported language: ${language}`);
    }

    // Update i18next
    await i18n.changeLanguage(language);
    setCurrentLanguage(language);

    // Save to backend if user is authenticated
    if (user) {
      try {
        const response = await fetch('/api/v1/users/settings', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ language }),
        });

        if (!response.ok) {
          console.warn('Failed to save language preference to backend');
        }
      } catch (error) {
        console.warn('Failed to save language preference:', error);
      }
    }

    // Save to localStorage
    localStorage.setItem('preferred-language', language);
    localStorage.setItem('pipline_language', language);
    
    // Reload page to ensure all components update with new language
    window.location.reload();
  };

  const value: LanguageContextType = {
    currentLanguage,
    setLanguage,
    t,
    isLoading,
    supportedLanguages: SUPPORTED_LANGUAGES,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
