import React, { useState, useEffect } from 'react';
import { useTabPersistence } from '../hooks/useTabPersistence';
import { useLanguage } from '../contexts/LanguageContext';
import { api } from '../utils/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import { UnifiedSection, UnifiedGrid, UnifiedCard, UnifiedButton, UnifiedWrapper } from '../design-system';
import { Button } from '../components/ui/button';
import { Breadcrumb } from '../components/ui';
import { Globe } from 'lucide-react';

interface TranslationKey {
  id: number;
  key_path: string;
  description: string;
  context: string;
  created_at: string;
  updated_at: string;
}

interface Translation {
  id: number;
  key_path: string;
  language_code: string;
  translation_text: string;
  is_approved: boolean;
  is_auto_translated: boolean;
  confidence_score: number;
  created_at: string;
  updated_at: string;
}

interface CustomDictionaryEntry {
  id: number;
  source_language: string;
  target_language: string;
  source_term: string;
  target_term: string;
  context: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface TranslationStats {
  total_keys: number;
  total_translations: number;
  auto_translated: number;
  approved: number;
  language_stats: Record<string, number>;
  custom_dictionary_entries: number;
  translation_memory_entries: number;
  completion_rate: number;
}

interface Tab {
  id: string;
  name: string;
  icon: string;
}

const SUPPORTED_LANGUAGES = {
  en: { name: 'English', flag: '🇺🇸' },
  tr: { name: 'Türkçe', flag: '🇹🇷' },
  es: { name: 'Español', flag: '🇪🇸' },
  fr: { name: 'Français', flag: '🇫🇷' },
  de: { name: 'Deutsch', flag: '🇩🇪' },
  it: { name: 'Italiano', flag: '🇮🇹' },
  pt: { name: 'Português', flag: '🇵🇹' },
  ru: { name: 'Русский', flag: '🇷🇺' },
  ja: { name: '日本語', flag: '🇯🇵' },
  ko: { name: '한국어', flag: '🇰🇷' },
  zh: { name: '中文', flag: '🇨🇳' },
  ar: { name: 'العربية', flag: '🇸🇦' }
};

export default function TranslationManager() {
  const { t } = useLanguage();
  const [activeTab, handleTabChange] = useTabPersistence('overview');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<TranslationStats | null>(null);
  const [translationKeys, setTranslationKeys] = useState<TranslationKey[]>([]);
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [customDictionary, setCustomDictionary] = useState<CustomDictionaryEntry[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState('tr');
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddKeyModal, setShowAddKeyModal] = useState(false);
  const [showAddTranslationModal, setShowAddTranslationModal] = useState(false);
  const [showAddDictionaryModal, setShowAddDictionaryModal] = useState(false);
  const [newKeyData, setNewKeyData] = useState({ key_path: '', description: '', context: '' });
  const [newTranslationData, setNewTranslationData] = useState({ key_path: '', language: '', text: '', is_approved: false });
  const [newDictionaryData, setNewDictionaryData] = useState({ source_language: 'en', target_language: 'tr', source_term: '', target_term: '', context: '' });

  const tabs: Tab[] = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'keys', name: 'Translation Keys', icon: '🔑' },
    { id: 'translations', name: 'Translations', icon: '🌐' },
    { id: 'dictionary', name: 'Custom Dictionary', icon: '📚' },
    { id: 'automation', name: 'Automation', icon: '⚙️' },
    { id: 'sync', name: 'Sync & Export', icon: '🔄' }
  ];

  useEffect(() => {
    loadStats();
    loadTranslationKeys();
    loadTranslations();
    loadCustomDictionary();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/translations/stats');
      const data = await response.json();
      if (data?.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTranslationKeys = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/translations/keys');
      const data = await response.json();
      if (data?.success) {
        setTranslationKeys(data.data);
      }
    } catch (error) {
      console.error('Error loading translation keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTranslations = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/translations/translations?language=${selectedLanguage}`);
      const data = await response.json();
      if (data?.success) {
        setTranslations(data.data);
      }
    } catch (error) {
      console.error('Error loading translations:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomDictionary = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/translations/custom-dictionary');
      const data = await response.json();
      if (data?.success) {
        setCustomDictionary(data.data);
      }
    } catch (error) {
      console.error('Error loading custom dictionary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddKey = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/translations/keys', newKeyData);
      const data = await response.json();
      if (data?.success) {
        setShowAddKeyModal(false);
        setNewKeyData({ key_path: '', description: '', context: '' });
        loadTranslationKeys();
        loadStats();
      }
    } catch (error) {
      console.error('Error adding translation key:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTranslation = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/translations/translations', newTranslationData);
      const data = await response.json();
      if (data?.success) {
        setShowAddTranslationModal(false);
        setNewTranslationData({ key_path: '', language: '', text: '', is_approved: false });
        loadTranslations();
        loadStats();
      }
    } catch (error) {
      console.error('Error adding translation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDictionaryEntry = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/translations/custom-dictionary', newDictionaryData);
      const data = await response.json();
      if (data?.success) {
        setShowAddDictionaryModal(false);
        setNewDictionaryData({ source_language: 'en', target_language: 'tr', source_term: '', target_term: '', context: '' });
        loadCustomDictionary();
        loadStats();
      }
    } catch (error) {
      console.error('Error adding dictionary entry:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoTranslate = async (keyPath: string, targetLanguage: string) => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/translations/auto-translate', {
        key_path: keyPath,
        target_language: targetLanguage
      });
      const data = await response.json();
      if (data?.success) {
        loadTranslations();
        loadStats();
      }
    } catch (error) {
      console.error('Error auto translating:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncFromJson = async (language: string) => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/translations/sync-from-json', { language });
      const data = await response.json();
      if (data?.success) {
        loadTranslationKeys();
        loadTranslations();
        loadStats();
      }
    } catch (error) {
      console.error('Error syncing from JSON:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Statistics Overview Section */}
      <Section title="Translation Statistics" subtitle="Overview of your translation system">
        <CardGrid cols={4} gap="lg">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-2xl">🔑</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Keys</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.total_keys || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-2xl">🌐</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Translations</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.total_translations || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-2xl">⚙️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Auto Translated</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.auto_translated || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-2xl">📚</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Custom Dictionary</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.custom_dictionary_entries || 0}</p>
              </div>
            </div>
          </div>
        </CardGrid>
      </Section>

      {/* Language Statistics Section */}
      <Section title="Language Coverage" subtitle="Translation statistics by language">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
            <div key={code} className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{lang.flag}</div>
              <div className="text-sm font-medium text-gray-900">{lang.name}</div>
              <div className="text-lg font-bold text-blue-600">{stats?.language_stats[code] || 0}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* Completion Rate Section */}
      <Section title="Translation Progress" subtitle="Overall completion rate across all languages">
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div 
            className="bg-blue-600 h-4 rounded-full transition-all duration-300"
            style={{ width: `${stats?.completion_rate || 0}%` }}
          ></div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {stats?.completion_rate.toFixed(1) || 0}% complete across all languages
        </p>
      </Section>
    </div>
  );

  const renderTranslationKeys = () => (
    <Section title="Translation Keys" subtitle="Manage and organize your translation keys">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search keys..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
            />
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowAddKeyModal(true)}
            className="flex items-center gap-2"
          >
            <span>➕</span>
            Add Key
          </Button>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key Path</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Context</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {translationKeys
                .filter(key => key.key_path.toLowerCase().includes(searchTerm.toLowerCase()))
                .map((key) => (
                  <tr key={key.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{key.key_path}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{key.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{key.context}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(key.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </Section>
  );

  const renderTranslations = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex space-x-4">
          <select
            value={selectedLanguage}
            onChange={(e) => {
              setSelectedLanguage(e.target.value);
              loadTranslations();
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
          >
            {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
              <option key={code} value={code}>
                {lang.flag} {lang.name}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={() => setShowAddTranslationModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Translation
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key Path</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Translation</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {translations.map((translation) => (
              <tr key={translation.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{translation.key_path}</td>
                <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">{translation.translation_text}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    translation.is_approved 
                      ? 'bg-green-100 text-green-800' 
                      : translation.is_auto_translated 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-gray-100 text-gray-800'
                  }`}>
                    {translation.is_approved ? 'Approved' : translation.is_auto_translated ? 'Auto' : 'Pending'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <button
                    onClick={() => handleAutoTranslate(translation.key_path, selectedLanguage)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    Auto Translate
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderCustomDictionary = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Custom Dictionary Entries</h3>
        <button
          onClick={() => setShowAddDictionaryModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Entry
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source Term</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target Term</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {customDictionary.map((entry) => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {SUPPORTED_LANGUAGES[entry.source_language as keyof typeof SUPPORTED_LANGUAGES]?.flag} {entry.source_language}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {SUPPORTED_LANGUAGES[entry.target_language as keyof typeof SUPPORTED_LANGUAGES]?.flag} {entry.target_language}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{entry.source_term}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{entry.target_term}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{entry.usage_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderAutomation = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Bulk Translation</h3>
        <p className="text-gray-600 mb-4">
          Automatically translate multiple keys using custom dictionary and translation memory.
        </p>
        <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
          Start Bulk Translation
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Missing Translations</h3>
        <p className="text-gray-600 mb-4">
          Find and translate missing translations across all languages.
        </p>
        <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors">
          Find Missing Translations
        </button>
      </div>
    </div>
  );

  const renderSyncExport = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Sync from JSON Files</h3>
        <p className="text-gray-600 mb-4">
          Import translations from existing JSON locale files into the database.
        </p>
        <div className="flex space-x-4">
          {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
            <button
              key={code}
              onClick={() => handleSyncFromJson(code)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {lang.flag} {code.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Export to JSON</h3>
        <p className="text-gray-600 mb-4">
          Export translations from database back to JSON format.
        </p>
        <div className="flex space-x-4">
          {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
            <button
              key={code}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              {lang.flag} {code.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'keys':
        return renderTranslationKeys();
      case 'translations':
        return renderTranslations();
      case 'dictionary':
        return renderCustomDictionary();
      case 'automation':
        return renderAutomation();
      case 'sync':
        return renderSyncExport();
      default:
        return renderOverview();
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <>
      <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Globe className="h-8 w-8 text-gray-600" />
              Translation Manager
            </h1>
            <p className="text-gray-600">Manage translations and dictionaries</p>
          </div>
          <div className='flex items-center gap-3'>
            <Button variant="outline" size="sm" className="flex items-center gap-2">
              <span>🔄</span>
              Sync
            </Button>
            <Button variant="outline" size="sm" className="flex items-center gap-2">
              <span>📤</span>
              Export
            </Button>
            <Button variant="primary" size="sm" className="flex items-center gap-2">
              <span>➕</span>
              Add Key
            </Button>
          </div>
        </div>
      </div>

        {/* Tabs */}
        <div className='bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-8'>
          <div className='bg-gradient-to-r from-gray-50 to-gray-100/50 px-6 py-2'>
            <nav className='flex space-x-1'>
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'bg-white text-blue-600 shadow-md border border-gray-200'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                  }`}
                >
                  <span>{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        <ContentArea>
          {renderContent()}
        </ContentArea>

        {/* Modals */}
        {showAddKeyModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Add Translation Key</h3>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Key path (e.g., common.loading)"
                    value={newKeyData.key_path}
                    onChange={(e) => setNewKeyData({ ...newKeyData, key_path: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                  <input
                    type="text"
                    placeholder="Description"
                    value={newKeyData.description}
                    onChange={(e) => setNewKeyData({ ...newKeyData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                  <input
                    type="text"
                    placeholder="Context (optional)"
                    value={newKeyData.context}
                    onChange={(e) => setNewKeyData({ ...newKeyData, context: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowAddKeyModal(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddKey}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add Key
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showAddTranslationModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Add Translation</h3>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Key path"
                    value={newTranslationData.key_path}
                    onChange={(e) => setNewTranslationData({ ...newTranslationData, key_path: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                  <select
                    value={newTranslationData.language}
                    onChange={(e) => setNewTranslationData({ ...newTranslationData, language: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    <option value="">Select Language</option>
                    {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
                      <option key={code} value={code}>
                        {lang.flag} {lang.name}
                      </option>
                    ))}
                  </select>
                  <textarea
                    placeholder="Translation text"
                    value={newTranslationData.text}
                    onChange={(e) => setNewTranslationData({ ...newTranslationData, text: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                    rows={3}
                  />
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={newTranslationData.is_approved}
                      onChange={(e) => setNewTranslationData({ ...newTranslationData, is_approved: e.target.checked })}
                      className="mr-2"
                    />
                    Approved
                  </label>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowAddTranslationModal(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddTranslation}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add Translation
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {showAddDictionaryModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Add Dictionary Entry</h3>
                <div className="space-y-4">
                  <select
                    value={newDictionaryData.source_language}
                    onChange={(e) => setNewDictionaryData({ ...newDictionaryData, source_language: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
                      <option key={code} value={code}>
                        {lang.flag} {lang.name}
                      </option>
                    ))}
                  </select>
                  <select
                    value={newDictionaryData.target_language}
                    onChange={(e) => setNewDictionaryData({ ...newDictionaryData, target_language: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    {Object.entries(SUPPORTED_LANGUAGES).map(([code, lang]) => (
                      <option key={code} value={code}>
                        {lang.flag} {lang.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    placeholder="Source term"
                    value={newDictionaryData.source_term}
                    onChange={(e) => setNewDictionaryData({ ...newDictionaryData, source_term: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                  <input
                    type="text"
                    placeholder="Target term"
                    value={newDictionaryData.target_term}
                    onChange={(e) => setNewDictionaryData({ ...newDictionaryData, target_term: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                  <input
                    type="text"
                    placeholder="Context (optional)"
                    value={newDictionaryData.context}
                    onChange={(e) => setNewDictionaryData({ ...newDictionaryData, context: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowAddDictionaryModal(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddDictionaryEntry}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add Entry
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
