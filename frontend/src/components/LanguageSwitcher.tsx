import React from 'react';
import { useLanguage, LanguageCode } from '../contexts/LanguageContext';

interface LanguageSwitcherProps {
  className?: string;
  variant?: 'button' | 'dropdown';
}

const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({ 
  className = '', 
  variant = 'button' 
}) => {
  const { currentLanguage, setLanguage, supportedLanguages } = useLanguage();

  const languages = Object.entries(supportedLanguages).map(([code, info]) => ({
    code: code as LanguageCode,
    name: info.name,
  }));

  const changeLanguage = async (langCode: string) => {
    try {
      await setLanguage(langCode as LanguageCode);
      console.log(`Language changed to: ${langCode}`);
    } catch (error) {
      console.error('Error changing language:', error);
    }
  };

  if (variant === 'button') {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => changeLanguage(lang.code)}
            className={`
              px-3 py-1.5 rounded-md text-sm font-medium transition-all
              ${
                currentLanguage === lang.code
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
            title={lang.name}
          >
            {lang.code.toUpperCase()}
          </button>
        ))}
      </div>
    );
  }

  // Dropdown variant
  return (
    <div className={`relative inline-block ${className}`}>
      <select
        value={currentLanguage}
        onChange={(e) => changeLanguage(e.target.value)}
        className="
          appearance-none bg-white border border-gray-300 rounded-md 
          px-4 py-2 pr-8 text-sm font-medium text-gray-700
          hover:border-gray-400 focus:outline-none focus:ring-2 
          focus:ring-blue-500 focus:border-transparent
          cursor-pointer transition-all
        "
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.name}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
          <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
        </svg>
      </div>
    </div>
  );
};

export default LanguageSwitcher;

