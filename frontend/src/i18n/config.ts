import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import existing translation files (flat structure with dot notation)
import translationsEN from '../locales/en.json';
import translationsTR from '../locales/tr.json';

// Translation resources - use "translation" as the namespace for flat structure
const resources = {
  en: {
    translation: translationsEN,
  },
  tr: {
    translation: translationsTR,
  },
};

i18n
  .use(LanguageDetector) // Detect user language
  .use(initReactI18next) // Pass i18n to react-i18next
  .init({
    resources,
    // Don't set 'lng' to allow LanguageDetector to work
    fallbackLng: 'en', // Fallback language if detection fails
    defaultNS: 'translation', // Use 'translation' as default namespace
    
    // Enable key separator for nested keys (e.g., "clients.title")
    keySeparator: '.',
    
    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'], // Save language preference
      lookupLocalStorage: 'pipline_language',
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    react: {
      useSuspense: false, // Disable suspense to avoid loading issues
    },
    
    debug: false, // Set to true for debugging
  });

export default i18n;

