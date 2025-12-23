import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTabPersistence } from '../hooks/useTabPersistence';

import {
  Settings as SettingsIcon,
  Users,
  Lock,
  Activity,
  FileText,
  Bell,
  Globe,
  Zap,
  Calendar,
  UserCheck,
  Building,
  TrendingUp,
  List,
  Plus,
  Edit,
  Trash2,
  X,
  Mail,
  Phone,
  RefreshCw,
  BarChart3,
  Download,
  CheckCircle,
  Clock,
  Circle,
  Building2,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  AlertCircle,
  Percent,
  Save,
  ChevronDown,
  Check,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { api } from '../utils/apiClient';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { SectionHeader } from '../components/ui/SectionHeader';
import { UnifiedCard, UnifiedButton, UnifiedBadge, UnifiedSection, UnifiedGrid } from '../design-system';
import EnhancedErrorBoundary from '../components/EnhancedErrorBoundary';
import {
  Breadcrumb,
  QuickActions,
  useKeyboardShortcuts,
  COMMON_SHORTCUTS
} from '../components/ui';

interface Tab {
  id: string;
  name: string;
  icon: any;
  content: React.ReactNode;
}

interface DropdownOption {
  id: number;
  value: string;
  commission_rate?: number;
  created_at?: string;
}

interface GroupedOptions {
  [fieldName: string]: DropdownOption[];
}

interface FieldType {
  value: string;
  label: string;
  requiresCommission: boolean;
  isStatic?: boolean;
  staticValues?: string[];
  isProtected?: boolean;
}

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [activeTab, handleTabChange] = useTabPersistence<'general' | 'dropdowns' | 'departments' | 'notifications' | 'integrations' | 'translations'>('general');
  const { t, currentLanguage, setLanguage, supportedLanguages } = useLanguage();
  const [isFieldTypeDropdownOpen, setIsFieldTypeDropdownOpen] = useState(false);

  // Fallback values in case language context is not available
  const safeCurrentLanguage = currentLanguage || 'en';
  const safeSupportedLanguages = supportedLanguages || { en: { flag: '🇺🇸', name: 'English' }, tr: { flag: '🇹🇷', name: 'Türkçe' } };

  // Check URL parameters for initial tab and monitor view
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    const viewParam = searchParams.get('view');

    // Legacy: Settings Admin tab moved to dedicated Admin Settings page
    if (tabParam === 'admin') {
      const qs = new URLSearchParams();
      if (viewParam) qs.set('view', viewParam);
      navigate(`/admin/settings${qs.toString() ? `?${qs.toString()}` : ''}`, { replace: true });
      return;
    }

    if (
      tabParam &&
      [
        'general',
        'dropdowns',
        'departments',
        'notifications',
        'integrations',
        'translations',
      ].includes(tabParam)
    ) {
      handleTabChange(tabParam);
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isFieldTypeDropdownOpen) {
        const target = event.target as HTMLElement;
        if (!target.closest('.custom-dropdown-container')) {
          setIsFieldTypeDropdownOpen(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isFieldTypeDropdownOpen]);

  // Dropdown management state
  const [dropdownOptions, setDropdownOptions] = useState<GroupedOptions>({});
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedOption, setSelectedOption] = useState<DropdownOption | null>(
    null
  );
  const [editingOption, setEditingOption] = useState<DropdownOption | null>(
    null
  );
  const [formData, setFormData] = useState({
    field_name: '',
    value: '',
    commission_rate: '',
  });
  const [securityCode, setSecurityCode] = useState('');

  // Department management state
  const [departments, setDepartments] = useState<string[]>([
    'Conversion', 'Retention', 'Marketing', 'Research', 'Operation', 'Management', 'Facility'
  ]);
  const [loadingDepartments, setLoadingDepartments] = useState(false);
  const [showDepartmentModal, setShowDepartmentModal] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<string>('');
  const [newDepartment, setNewDepartment] = useState('');
  const [isEditingDepartment, setIsEditingDepartment] = useState(false);

  const fieldTypes = [
    // Static fields (cannot be modified)
    {
      value: 'payment_method',
      label: t('settings.payment_method'),
      requiresCommission: false,
      isStatic: true,
      staticValues: ['Bank', 'Credit card', 'Tether']
    },
    {
      value: 'currency',
      label: t('settings.currency'),
      requiresCommission: false,
      isStatic: true,
      staticValues: ['TL', 'USD', 'EUR']
    },
    {
      value: 'category',
      label: t('settings.category'),
      requiresCommission: false,
      isStatic: true,
      staticValues: ['DEP', 'WD']
    },
    // Dynamic fields (can be managed)
    { value: 'psp', label: t('settings.psp_kasa'), requiresCommission: true, isStatic: false, isProtected: false },
    { value: 'company', label: t('settings.company'), requiresCommission: false, isStatic: false, isProtected: false },
  ];

  // Fetch dropdown options
  const fetchDropdownOptions = async () => {
    try {
      setLoadingOptions(true);
      const response = await api.get('/transactions/dropdown-options');

      if (response.ok) {
        const data = await api.parseResponse(response) as GroupedOptions;
        // Debug logging removed for production
        setDropdownOptions(data || {} as GroupedOptions);
      } else {
        console.error('Failed to fetch dropdown options');
      }
    } catch (error) {
      console.error('Error fetching dropdown options:', error);
    } finally {
      setLoadingOptions(false);
    }
  };

  // Department management functions
  const fetchDepartments = async () => {
    try {
      setLoadingDepartments(true);
      // Load departments from localStorage or use default
      const savedDepartments = localStorage.getItem('systemDepartments');
      if (savedDepartments) {
        setDepartments(JSON.parse(savedDepartments));
      } else {
        // Default departments
        const defaultDepartments = [
          'Conversion', 'Retention', 'Marketing', 'Research', 'Operation', 'Management', 'Facility'
        ];
        setDepartments(defaultDepartments);
        localStorage.setItem('systemDepartments', JSON.stringify(defaultDepartments));
      }
    } catch (error) {
      console.error('Error fetching departments:', error);
    } finally {
      setLoadingDepartments(false);
    }
  };

  const handleAddDepartment = async () => {
    if (!newDepartment.trim()) return;

    try {
      // Check if department already exists
      if (departments.includes(newDepartment.trim())) {
        alert(t('settings.department_exists'));
        return;
      }

      const updatedDepartments = [...departments, newDepartment.trim()];
      setDepartments(updatedDepartments);

      // Save to localStorage
      localStorage.setItem('systemDepartments', JSON.stringify(updatedDepartments));

      setNewDepartment('');
      setShowDepartmentModal(false);

      // Department added successfully
    } catch (error) {
      console.error('Error adding department:', error);
    }
  };

  const handleEditDepartment = async () => {
    if (!editingDepartment.trim()) return;

    try {
      // Find the original department name being edited
      const originalDepartment = departments.find(dept => dept !== editingDepartment);
      if (!originalDepartment) {
        alert(t('settings.department_not_found'));
        return;
      }

      // Check if new name already exists
      if (departments.includes(editingDepartment.trim()) && editingDepartment.trim() !== originalDepartment) {
        alert(t('settings.department_name_exists'));
        return;
      }

      const updatedDepartments = departments.map(dept =>
        dept === originalDepartment ? editingDepartment.trim() : dept
      );
      setDepartments(updatedDepartments);

      // Save to localStorage
      localStorage.setItem('systemDepartments', JSON.stringify(updatedDepartments));

      setEditingDepartment('');
      setIsEditingDepartment(false);
      setShowDepartmentModal(false);

      // Department updated successfully
    } catch (error) {
      console.error('Error updating department:', error);
    }
  };

  const handleDeleteDepartment = async (department: string) => {
    if (!confirm(`Are you sure you want to delete the department "${department}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const updatedDepartments = departments.filter(dept => dept !== department);
      setDepartments(updatedDepartments);

      // Save to localStorage
      localStorage.setItem('systemDepartments', JSON.stringify(updatedDepartments));

      // Department deleted successfully
    } catch (error) {
      console.error('Error deleting department:', error);
    }
  };

  const openDepartmentModal = (department?: string) => {
    if (department) {
      setEditingDepartment(department);
      setIsEditingDepartment(true);
    } else {
      setNewDepartment('');
      setIsEditingDepartment(false);
    }
    setShowDepartmentModal(true);
  };

  useEffect(() => {
    if (activeTab === 'dropdowns') {
      fetchDropdownOptions();
    }
    if (activeTab === 'departments') {
      fetchDepartments();
    }
  }, [activeTab]);

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      key: '1',
      ctrlKey: true,
      action: () => handleTabChange('general')
    },
    {
      key: '2',
      ctrlKey: true,
      action: () => handleTabChange('dropdowns')
    },
    {
      key: '3',
      ctrlKey: true,
      action: () => handleTabChange('departments')
    },
    {
      key: '4',
      ctrlKey: true,
      action: () => handleTabChange('admin')
    },
    {
      key: '5',
      ctrlKey: true,
      action: () => handleTabChange('notifications')
    },
    {
      key: '6',
      ctrlKey: true,
      action: () => handleTabChange('integrations')
    },
    {
      key: '7',
      ctrlKey: true,
      action: () => handleTabChange('translations')
    }
  ]);

  const handleLanguageChange = async (language: string) => {
    try {
      await setLanguage(language as any);
    } catch (error) {
      console.error('Failed to change language:', error);
    }
  };

  // Dropdown management functions
  const handleAddOption = async () => {
    // Validate form data before sending
    if (!formData.field_name) {
      console.error('Validation Error:', 'Please select a field type');
      return;
    }

    // Check if this is a protected field and validate security code
    const fieldType = fieldTypes.find(f => f.value === formData.field_name);
    if (fieldType?.isProtected) {
      if (!securityCode.trim()) {
        console.error('Security Required:', 'Security code is required for adding protected options');
        return;
      }
      if (securityCode.trim() !== '4561') {
        console.error('Invalid Code:', 'Invalid security code');
        return;
      }
    }

    if (!formData.value.trim()) {
      console.error('Validation Error:', 'Option value is required');
      return;
    }

    // Check for duplicate values
    const currentOptions = dropdownOptions[formData.field_name] || [];
    const duplicateOption = currentOptions.find(option =>
      option.value === formData.value.trim()
    );

    if (duplicateOption) {
      console.error('Duplicate Option:', `An option with the value "${formData.value.trim()}" already exists for ${fieldType?.label || formData.field_name} field`);
      return;
    }

    // For PSP options, validate commission rate
    let finalCommissionRate = null;
    if (formData.field_name === 'psp') {
      if (!formData.commission_rate || formData.commission_rate.trim() === '') {
        alert('Commission rate is required for PSP options');
        return;
      }

      let commissionRate = parseFloat(formData.commission_rate);
      if (isNaN(commissionRate)) {
        alert('Commission rate must be a valid number');
        return;
      }

      // Eger kullanici yuzde olarak girerse (>1), otomatik olarak decimal'e cevir
      // Ornegin: 2.5 -> 0.025, 5 -> 0.05
      if (commissionRate > 1) {
        commissionRate = commissionRate / 100;
      }

      if (commissionRate < 0 || commissionRate > 1) {
        alert('Commission rate must be between 0 and 100% (enter as decimal: 0.025 for 2.5% or as percentage: 2.5)');
        return;
      }
      
      finalCommissionRate = commissionRate.toString();
    }

    try {
      // Session-based authentication provides CSRF protection
      const response = await api.post(
        '/transactions/dropdown-options',
        {
          field_name: formData.field_name,
          value: formData.value.trim(),
          commission_rate: finalCommissionRate,
        }
      );

      // Check for successful response (200-299 status codes)
      if (response.ok || response.status === 201) {
        setShowAddModal(false);
        setFormData({ field_name: '', value: '', commission_rate: '' });
        setSecurityCode('');
        await fetchDropdownOptions();

      } else {
        console.error('Add failed - response status:', response.status);

        // Handle error response
        let errorMessage = t('settings.failed_to_add_option');
        try {
          const errorData = response.data as any || {};
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
        }

        alert(errorMessage);
      }
    } catch (error) {
      console.error('Error adding option:', error);
    }
  };

  const handleEditOption = async () => {
    if (!editingOption) return;

    // Check if this is a protected field and validate security code
    const fieldType = fieldTypes.find(f => f.value === formData.field_name);
    if (fieldType?.isProtected) {
      if (!securityCode.trim()) {
        alert(t('settings.security_code_required'));
        return;
      }
      if (securityCode.trim() !== '4561') {
        alert(t('settings.invalid_security_code'));
        return;
      }
    }

    // Check for duplicate values (excluding current option)
    const currentOptions = dropdownOptions[formData.field_name] || [];
    // Debug logging removed for production

    const duplicateOption = currentOptions.find(option =>
      option.value === formData.value.trim() && option.id !== editingOption.id
    );

    if (duplicateOption) {
      // Duplicate option found
      alert(
        t('settings.option_value_exists')
          .replace('{value}', formData.value.trim())
          .replace('{field}', fieldType?.label || formData.field_name)
      );
      return;
    }

    // Validate form data before sending
    if (!formData.value.trim()) {
      console.error('Validation Error:', 'Option value is required');
      return;
    }

    // For PSP options, validate commission rate
    let finalCommissionRate = null;
    if (formData.field_name === 'psp') {
      if (!formData.commission_rate || formData.commission_rate.trim() === '') {
        alert('Commission rate is required for PSP options');
        return;
      }

      let commissionRate = parseFloat(formData.commission_rate);
      if (isNaN(commissionRate)) {
        alert('Commission rate must be a valid number');
        return;
      }

      // Eger kullanici yuzde olarak girerse (>1), otomatik olarak decimal'e cevir
      // Ornegin: 2.5 -> 0.025, 5 -> 0.05
      if (commissionRate > 1) {
        commissionRate = commissionRate / 100;
      }

      if (commissionRate < 0 || commissionRate > 1) {
        alert('Commission rate must be between 0 and 100% (enter as decimal: 0.025 for 2.5% or as percentage: 2.5)');
        return;
      }
      
      finalCommissionRate = commissionRate.toString();
    }

    try {
      // Session-based authentication provides CSRF protection
      const response = await api.put(
        `/transactions/dropdown-options/${editingOption.id}`,
        {
          value: formData.value.trim(),
          commission_rate: finalCommissionRate,
        }
      );

      if (response.ok) {
        // Parse response to get updated data
        try {
          const responseData = await api.parseResponse(response);

        } catch (parseError) {
          console.warn('Could not parse response, but update was successful');
        }

        setShowEditModal(false);
        setEditingOption(null);
        setFormData({ field_name: '', value: '', commission_rate: '' });
        setSecurityCode('');

        // Force refresh dropdown options (bypass cache)
        try {
          setLoadingOptions(true);
          const refreshResponse = await api.get('/transactions/dropdown-options');
          if (refreshResponse.ok) {
            const data = await api.parseResponse(refreshResponse) as GroupedOptions;
            setDropdownOptions(data || {} as GroupedOptions);

          }
        } catch (refreshError) {
          console.error('Error refreshing options:', refreshError);
          // Fallback: still try to fetch normally
          await fetchDropdownOptions();
        } finally {
          setLoadingOptions(false);
        }

        // İşlem başarılı olduktan sonra token'i temizle
        api.clearToken();

      } else {
        console.error('Update failed - response status:', response.status);
        console.error('Update failed - response:', response);

        // Handle error response directly without parseResponse
        let errorMessage = 'Failed to update option';
        try {
          const errorData = response.data as any || {};
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
        }

        console.error('Update failed - error message:', errorMessage);
      }
    } catch (error) {
      console.error('Error updating option:', error);
      // Check if it's a parsed error with a specific message
      const errorMessage = error instanceof Error ? error.message : 'Failed to update option. Please try again.';
      alert(errorMessage);
    }
  };

  const handleDeleteOption = async (option: DropdownOption, fieldName: string) => {
    // Check if this is a protected field (PSP or Company)
    const fieldType = fieldTypes.find(f => f.value === fieldName);
    const isProtected = fieldType?.isProtected || false;

    if (isProtected) {
      // Enhanced confirmation for protected fields
      const confirmMessage = t('settings.delete_protected_warning', { field: fieldType?.label || 'Unknown' });

      const userInput = prompt(confirmMessage);
      if (userInput !== 'DELETE') {
        alert(t('settings.must_type_delete'));
        return;
      }

      // Second confirmation for critical options
      const finalConfirm = confirm(t('settings.final_delete_warning', {
        option: option.value,
        field: fieldType?.label || 'Unknown'
      }));

      if (!finalConfirm) {
        alert(t('settings.deletion_cancelled'));
        return;
      }
    } else {
      // Standard confirmation for non-protected fields
      if (!confirm('Are you sure you want to delete this option?')) return;
    }

    try {
      // Token'i temizle ve yeni token al
      api.clearToken();
      
      // Yeni token alınmasını bekle (CSRF doğrulaması için kritik)      
      // Session-based authentication provides CSRF protection
      const response = await api.delete(
        `/transactions/dropdown-options/${option.id}`
      );
      if (response.ok) {
        await fetchDropdownOptions();
        // İşlem başarılı olduktan sonra token'i temizle
        api.clearToken();

      } else {
        console.error('Delete failed - response status:', response.status);

        // Handle error response directly without parseResponse
        let errorMessage = 'Failed to delete option';
        try {
          const errorData = response.data as any || {};
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
        }

        console.error('Delete Failed:', errorMessage);
      }
    } catch (error) {
      console.error('Error deleting option:', error);
    }
  };

  const openEditModal = (option: DropdownOption, fieldName: string) => {
    setEditingOption(option);
    // Commission rate'i yuzde olarak goster (0.025 -> 2.5)
    const displayRate = option.commission_rate 
      ? (parseFloat(option.commission_rate.toString()) * 100).toString()
      : '';
    setFormData({
      field_name: fieldName,
      value: option.value,
      commission_rate: displayRate,
    });
    setSecurityCode(''); // Clear security code when opening modal
    setShowEditModal(true);
  };

  const tabs = [
    {
      id: 'general',
      label: t('settings.general'),
      icon: SettingsIcon,
      content: (
        <div className="space-y-6">
          {/* Company Information */}
          <Card className="border border-gray-200 shadow-sm">
            <CardHeader className="border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                  <Building className="h-5 w-5 text-slate-700" />
                </div>
                <div>
                  <CardTitle className="text-lg font-semibold text-gray-900">
                    {t('settings.company_information')}
                  </CardTitle>
                  <CardDescription className="text-sm text-gray-600">{t('settings.order_invest_pipeline_collab')}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <label className="block text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">
                    {t('settings.company_name')}
                  </label>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-semibold text-gray-900">Order Invest</span>
                    <span className="text-gray-400">×</span>
                    <span className="text-base font-semibold text-gray-700">PipLine</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{t('settings.strategic_partnership')}</p>
                </div>

                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <label className="block text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">
                    {t('settings.contact_email')}
                  </label>
                  <Input
                    type="email"
                    placeholder="contact@orderinvest.com"
                    className="bg-white border-gray-300"
                  />
                </div>
              </div>

              <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-md">
                <div className="flex items-start gap-2">
                  <div className="text-slate-600 mt-0.5">
                    <Activity className="h-4 w-4" />
                  </div>
                  <div className="text-sm text-slate-700">
                    <p className="font-medium mb-1">{t('settings.partnership_overview')}</p>
                    <p className="text-xs leading-relaxed text-slate-600">
                      {t('settings.partnership_description')}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Preferences */}
          <Card className="border border-gray-200 shadow-sm">
            <CardHeader className="border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                  <Globe className="h-5 w-5 text-slate-700" />
                </div>
                <div>
                  <CardTitle className="text-lg font-semibold text-gray-900">
                    {t('settings.system_preferences')}
                  </CardTitle>
                  <CardDescription className="text-sm text-gray-600">{t('settings.configure_system')}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <label className="block text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">
                    {t('settings.timezone')}
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-slate-500 focus:border-slate-500 transition-colors bg-white text-sm text-gray-900 appearance-none cursor-pointer"
                    style={{ zIndex: 9999 }}>
                    <option className="bg-white text-gray-900">Europe/Istanbul (UTC+3)</option>
                    <option className="bg-white text-gray-900">UTC</option>
                    <option className="bg-white text-gray-900">Europe/London (UTC+0)</option>
                    <option className="bg-white text-gray-900">America/New_York (UTC-5)</option>
                    <option className="bg-white text-gray-900">Asia/Dubai (UTC+4)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-2">{t('settings.default_europe_istanbul')}</p>
                </div>

                <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                  <label className="block text-xs font-medium text-gray-600 mb-2 uppercase tracking-wide">
                    {t('settings.language')}
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-slate-500 focus:border-slate-500 transition-colors bg-white text-sm text-gray-900 appearance-none cursor-pointer"
                    style={{ zIndex: 9999 }}
                    value={safeCurrentLanguage}
                    onChange={e => handleLanguageChange(e.target.value)}
                  >
                    {Object.entries(safeSupportedLanguages).map(([code, lang]) => (
                      <option key={code} value={code} className="bg-white text-gray-900">
                        {lang.flag} {lang.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-2">{t('settings.primary_turkish')}</p>
                </div>
              </div>

              <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-md">
                <div className="flex items-start gap-2">
                  <div className="text-slate-600 mt-0.5">
                    <Activity className="h-4 w-4" />
                  </div>
                  <div className="text-sm text-slate-700">
                    <p className="font-medium mb-1">{t('settings.currency_standard')}</p>
                    <p className="text-xs leading-relaxed text-slate-600">
                      {t('settings.currency_standard_desc')}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              size="lg"
              className="px-8 py-3 bg-slate-700 hover:bg-slate-800 text-white font-medium"
            >
              <Save className="h-4 w-4 mr-2" />
              {t('settings.save_config_changes')}
            </Button>
          </div>
        </div>
      ),
    },
    {
      id: 'dropdowns',
      label: t('settings.dropdown_management'),
      icon: List,
      content: (
        <div className="space-y-6">
          {/* Professional Header */}
          <Card className="border border-gray-200 shadow-sm">
            <CardHeader className="border-b border-gray-100 bg-gray-50/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <List className="h-5 w-5 text-slate-700" />
                  </div>
                  <div>
                    <CardTitle className="text-lg font-semibold text-gray-900">
                      {t('settings.dropdown_management')}
                    </CardTitle>
                    <CardDescription className="text-sm text-gray-600">
                      {t('settings.manage_dropdown_options')}
                    </CardDescription>
                  </div>
                </div>
                <Button
                  onClick={() => {
                    setSecurityCode(''); // Clear security code when opening modal
                    setShowAddModal(true);
                  }}
                  className="bg-slate-700 hover:bg-slate-800 text-white"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  {t('settings.add_new_option')}
                </Button>
              </div>
            </CardHeader>
          </Card>

          {/* Statistics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <span className="text-slate-700 font-semibold text-base">₺</span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{t('settings.currency_options')}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dropdownOptions['currency']?.length || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <span className="text-slate-700 font-semibold text-base">💳</span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{t('settings.payment_methods')}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dropdownOptions['payment_method']?.length || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <span className="text-slate-700 font-semibold text-base">🏢</span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{t('settings.psp_kasa')}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dropdownOptions['psp']?.length || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <span className="text-slate-700 font-semibold text-base">📊</span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{t('common.total_options')}</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Object.values(dropdownOptions).reduce((acc, curr) => acc + (curr?.length || 0), 0)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          {loadingOptions ? (
            <Card className="p-8 border border-gray-200">
              <CardContent className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-600 mx-auto mb-4"></div>
                <p className="text-gray-700 font-medium">{t('settings.loading_configuration_data')}</p>
                <p className="text-sm text-gray-500 mt-1">{t('settings.please_wait_retrieve_settings')}</p>
              </CardContent>
            </Card>
          ) : (
            <Card className="border border-gray-200 overflow-hidden">
              {/* Table Header */}
              <CardHeader className="px-6 py-4 border-b border-gray-200 bg-gray-50/50">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-semibold text-gray-900">
                    {t('settings.configuration_categories')}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs bg-slate-100 text-slate-700">
                      {Object.values(dropdownOptions).reduce((acc, curr) => acc + (curr?.length || 0), 0)} {t('settings.total_items')}
                    </Badge>
                  </div>
                </div>
              </CardHeader>

              {/* Configuration Categories */}
              <CardContent className="p-0">
                <div className="divide-y divide-gray-100">
                  {fieldTypes.map(fieldType => (
                    <div key={fieldType.value} className="p-6 hover:bg-gray-50 transition-colors duration-200">
                      <div className='flex items-center justify-between mb-4'>
                        <div className='flex items-center gap-4'>
                          <div className='w-12 h-12 bg-gradient-to-br from-gray-600 to-gray-600 rounded-lg flex items-center justify-center shadow-sm'>
                            <List className='h-6 w-6 text-white' />
                          </div>
                          <div>
                            <div className='flex items-center gap-2'>
                              <h5 className='text-lg font-bold text-gray-900'>
                                {fieldType.label}
                              </h5>
                              {fieldType.isProtected && (
                                <div className='flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium'>
                                  <Shield className='h-3 w-3' />
                                  {t('settings.protected')}
                                </div>
                              )}
                            </div>
                            <div className='flex items-center gap-3 mt-1'>
                              <span className='text-sm text-gray-600'>
                                {fieldType.isStatic
                                  ? `${fieldType.staticValues?.length || 0} ${t('settings.fixed_options')}`
                                  : `${dropdownOptions[fieldType.value]?.length || 0} ${t('settings.options_configured')}`
                                }
                              </span>
                              {fieldType.isStatic && (
                                <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                                  {t('settings.fixed_values')}
                                </span>
                              )}
                              {fieldType.isProtected && !fieldType.isStatic && (
                                <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800'>
                                  <Shield className='h-3 w-3 mr-1' />
                                  {t('settings.protected')}
                                </span>
                              )}
                              {fieldType.requiresCommission && (
                                <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800'>
                                  {t('settings.commission_required')}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {!fieldType.isStatic && (
                          <UnifiedButton
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setFormData(prev => ({ ...prev, field_name: fieldType.value }));
                              setShowAddModal(true);
                            }}
                            icon={<Plus className="h-4 w-4" />}
                            iconPosition="left"
                          >
                            Add {fieldType.label}
                          </UnifiedButton>
                        )}
                      </div>

                      {fieldType.isStatic ? (
                        /* Static fields - show fixed values */
                        <div className='bg-gray-50 rounded-lg p-4'>
                          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
                            {fieldType.staticValues?.map((value, index) => (
                              <div
                                key={index}
                                className='bg-white rounded-lg p-3 border border-gray-200 shadow-sm'
                              >
                                <div className='flex items-center justify-between'>
                                  <div className='flex-1'>
                                    <div className='flex items-center gap-2 mb-1'>
                                      <span className='font-semibold text-gray-900 text-sm'>
                                        {value}
                                      </span>
                                      <span className='inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                                        {t('settings.protected')}
                                      </span>
                                    </div>
                                    <p className='text-xs text-gray-500'>
                                      {t('settings.static_value')}
                                    </p>
                                  </div>
                                  <div className='flex items-center gap-1'>
                                    <Lock className='h-4 w-4 text-gray-400' />
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : dropdownOptions[fieldType.value]?.length > 0 ? (
                        /* Dynamic fields - show manageable options */
                        <div className='bg-gray-50 rounded-lg p-4'>
                          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
                            {dropdownOptions[fieldType.value].map(option => (
                              <div
                                key={option.id}
                                className='bg-white rounded-lg p-3 border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all duration-200'
                              >
                                <div className='flex items-center justify-between'>
                                  <div className='flex-1'>
                                    <div className='flex items-center gap-2 mb-1'>
                                      <span className='font-semibold text-gray-900 text-sm'>
                                        {option.value}
                                      </span>
                                      {option.value.toUpperCase() === 'TETHER' ? (
                                        <span className='inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800'>
                                          Internal KASA
                                        </span>
                                      ) : (option.commission_rate !== null && option.commission_rate !== undefined) ? (
                                        <span className='inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                                          {(Number(option.commission_rate) * 100).toFixed(1)}%
                                        </span>
                                      ) : null}
                                      {fieldType.isProtected && (
                                        <span className='inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800'>
                                          <Shield className='h-3 w-3 mr-1' />
                                          {t('settings.protected')}
                                        </span>
                                      )}
                                    </div>
                                    <p className='text-xs text-gray-500'>
                                      ID: {option.id} • {t('settings.created')}: {option.created_at ? new Date(option.created_at).toLocaleDateString() : 'N/A'}
                                    </p>
                                  </div>
                                  <div className='flex items-center gap-1'>
                                    <button
                                      onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        openEditModal(option, fieldType.value);
                                      }}
                                      className='p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded transition-colors duration-200'
                                      title={t('settings.edit_option')}
                                      type="button"
                                    >
                                      <Edit className='h-4 w-4' />
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        handleDeleteOption(option, fieldType.value);
                                      }}
                                      className={`p-1.5 rounded transition-colors duration-200 ${fieldType.isProtected
                                        ? 'text-red-400 hover:text-red-600 hover:bg-red-50'
                                        : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                                        }`}
                                      title={fieldType.isProtected ? t('settings.protected_option_warning') : t('settings.delete_option')}
                                      type="button"
                                    >
                                      <Trash2 className='h-4 w-4' />
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className='text-center py-8 bg-gray-50 rounded-lg'>
                          <div className='w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-3'>
                            <List className='h-8 w-8 text-gray-400' />
                          </div>
                          <h6 className='text-gray-600 font-medium mb-1'>No {fieldType.label} configured</h6>
                          <p className='text-sm text-gray-500 mb-3'>
                            Start building your {fieldType.label.toLowerCase()} configuration
                          </p>
                          <button
                            onClick={() => setShowAddModal(true)}
                            className='inline-flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 font-medium text-sm'
                          >
                            <Plus className='h-4 w-4' />
                            Add First {fieldType.label}
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      ),
    },
    {
      id: 'departments',
      label: t('settings.departments'),
      icon: Building,
      content: (
        <div className="space-y-6">
          {/* Professional Header */}
          <UnifiedCard variant="elevated" className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gray-100 rounded-full -translate-y-16 translate-x-16"></div>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-gray-700 to-gray-600 rounded-xl flex items-center justify-center shadow-lg">
                    <Building className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl font-bold text-gray-900">
                      {t('settings.department_management')}
                    </CardTitle>
                    <CardDescription className="text-gray-600 font-medium">
                      {t('settings.organizational_structure_desc')}
                    </CardDescription>
                  </div>
                </div>
                <UnifiedButton
                  variant="primary"
                  size="lg"
                  onClick={() => openDepartmentModal()}
                  icon={<Plus className="h-5 w-5" />}
                  iconPosition="left"
                  className="px-6 py-3 font-semibold shadow-lg hover:shadow-lg"
                >
                  {t('settings.add_new_department')}
                </UnifiedButton>
              </div>
            </CardContent>
          </UnifiedCard>

          {/* Statistics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UnifiedCard variant="outlined" className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-16 h-16 bg-gray-100 rounded-full -translate-y-8 translate-x-8"></div>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Building className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium">{t('settings.total_departments')}</p>
                    <p className="text-xl font-bold text-gray-900">
                      {departments.length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>

            <UnifiedCard variant="outlined" className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-16 h-16 bg-slate-100 rounded-full -translate-y-8 translate-x-8"></div>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <Users className="h-5 w-5 text-slate-700" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium">{t('settings.active_teams')}</p>
                    <p className="text-xl font-bold text-gray-900">
                      {departments.filter(dept => ['Conversion', 'Retention', 'Marketing', 'Research', 'Operation'].includes(dept)).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>

            <UnifiedCard variant="outlined" className="relative overflow-hidden">
              <div className="absolute top-0 right-0 w-16 h-16 bg-slate-100 rounded-full -translate-y-8 translate-x-8"></div>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-slate-700" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-medium">{t('settings.support_functions')}</p>
                    <p className="text-xl font-bold text-gray-900">
                      {departments.filter(dept => ['Management', 'Facility'].includes(dept)).length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </UnifiedCard>
          </div>

          {/* Main Content */}
          {loadingDepartments ? (
            <UnifiedCard variant="outlined" className="p-8">
              <CardContent className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-600 mx-auto mb-4"></div>
                <p className="text-gray-600 font-medium">{t('settings.loading_organizational_structure')}</p>
                <p className="text-sm text-gray-500 mt-1">{t('settings.please_wait_retrieve_department_config')}</p>
              </CardContent>
            </UnifiedCard>
          ) : (
            <UnifiedCard variant="outlined" className="overflow-hidden">
              {/* Table Header */}
              <div className='px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-50'>
                <div className='flex items-center justify-between'>
                  <h4 className='text-lg font-semibold text-gray-900'>
                    {t('settings.organizational_structure')}
                  </h4>
                  <div className='flex items-center gap-2'>
                    <span className='text-xs text-gray-500 bg-white px-2 py-1 rounded-full border border-gray-200'>
                      {departments.length} {t('settings.departments')}
                    </span>
                  </div>
                </div>
              </div>

              {departments.length === 0 ? (
                <div className='text-center py-12 px-6'>
                  <div className='w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4'>
                    <Building className='h-10 w-10 text-gray-400' />
                  </div>
                  <h3 className='text-lg font-semibold text-gray-900 mb-2'>
                    {t('settings.no_departments_configured')}
                  </h3>
                  <p className='text-gray-500 mb-6 max-w-md mx-auto text-sm'>
                    {t('settings.start_building_organizational_structure')}
                  </p>
                  <button
                    onClick={() => openDepartmentModal()}
                    className='inline-flex items-center px-6 py-3 border border-transparent rounded-lg text-sm font-medium text-white bg-gradient-to-r from-gray-700 to-gray-600 hover:from-gray-800 hover:to-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors shadow-sm'
                  >
                    <Plus className='h-4 w-4 mr-2' />
                    {t('settings.create_first_department')}
                  </button>
                </div>
              ) : (
                <div className='divide-y divide-gray-100'>
                  {departments.map((department, index) => (
                    <div key={index} className='p-6 hover:bg-gray-50 transition-colors duration-200'>
                      <div className='flex items-center justify-between'>
                        <div className='flex items-center gap-4'>
                          <div className='w-12 h-12 bg-gradient-to-br from-gray-600 to-gray-600 rounded-lg flex items-center justify-center shadow-sm'>
                            <Building className='h-6 w-6 text-white' />
                          </div>
                          <div>
                            <h4 className='text-lg font-bold text-gray-900'>
                              {department}
                            </h4>
                            <div className='flex items-center gap-3 mt-1'>
                              <span className='text-sm text-gray-600'>
                                {t('settings.department_id')}: {index + 1}
                              </span>
                              {['Conversion', 'Retention', 'Marketing', 'Research', 'Operation'].includes(department) && (
                                <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800'>
                                  {t('settings.core_team')}
                                </span>
                              )}
                              {['Management', 'Facility'].includes(department) && (
                                <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                                  {t('settings.support_function')}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className='flex items-center gap-2'>
                          <button
                            onClick={() => openDepartmentModal(department)}
                            className='inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 font-medium text-sm'
                            title={t('settings.edit')}
                          >
                            <Edit className='h-4 w-4' />
                            {t('settings.edit')}
                          </button>
                          <button
                            onClick={() => handleDeleteDepartment(department)}
                            className='inline-flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors duration-200 font-medium text-sm'
                            title={t('settings.delete')}
                          >
                            <Trash2 className='h-4 w-4' />
                            {t('settings.delete')}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </UnifiedCard>
          )}
        </div>
      ),
    },
    {
      id: 'notifications',
      label: t('settings.notifications'),
      icon: Bell,
      content: (
        <div className='space-y-6'>
          <div className='bg-gray-50 rounded-xl p-6 border border-slate-100'>
            <div className='flex items-center gap-3 mb-5'>
              <div className='w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center shadow-sm'>
                <Bell className='h-5 w-5 text-white' />
              </div>
              <div>
                <h3 className='text-lg font-bold text-gray-900'>
                  {t('settings.notifications_title')}
                </h3>
                <p className='text-sm text-gray-600'>{t('settings.configure_notifications')}</p>
              </div>
            </div>
            <div className='space-y-4'>
              <div className='bg-white rounded-lg p-5 border border-slate-200'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-3'>
                    <div className='w-8 h-8 bg-gradient-to-br from-gray-500 to-gray-600 rounded-lg flex items-center justify-center'>
                      <Mail className='h-4 w-4 text-white' />
                    </div>
                    <div>
                      <h4 className='font-semibold text-gray-900 text-sm'>
                        {t('settings.email_notifications_title')}
                      </h4>
                      <p className='text-xs text-gray-500'>
                        {t('settings.receive_important_updates')}
                      </p>
                    </div>
                  </div>
                  <label className='relative inline-flex items-center cursor-pointer'>
                    <input type='checkbox' className='sr-only peer' />
                    <div className="w-10 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-gray-500"></div>
                  </label>
                </div>
              </div>

              <div className='bg-white rounded-lg p-5 border border-slate-200'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-3'>
                    <div className='w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center'>
                      <Phone className='h-4 w-4 text-white' />
                    </div>
                    <div>
                      <h4 className='font-semibold text-gray-900 text-sm'>
                        {t('settings.sms_notifications_title')}
                      </h4>
                      <p className='text-xs text-gray-500'>
                        {t('settings.urgent_alerts_text')}
                      </p>
                    </div>
                  </div>
                  <label className='relative inline-flex items-center cursor-pointer'>
                    <input type='checkbox' className='sr-only peer' />
                    <div className="w-10 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-gray-500"></div>
                  </label>
                </div>
              </div>

              <div className='bg-white rounded-lg p-5 border border-slate-200'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-3'>
                    <div className='w-8 h-8 bg-slate-700 rounded-lg flex items-center justify-center'>
                      <Bell className='h-4 w-4 text-white' />
                    </div>
                    <div>
                      <h4 className='font-semibold text-gray-900 text-sm'>
                        {t('settings.push_notifications_title')}
                      </h4>
                      <p className='text-xs text-gray-500'>
                        {t('settings.realtime_browser_notifications')}
                      </p>
                    </div>
                  </div>
                  <label className='relative inline-flex items-center cursor-pointer'>
                    <input type='checkbox' className='sr-only peer' />
                    <div className="w-10 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-gray-500"></div>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'integrations',
      label: t('settings.integrations'),
      icon: Globe,
      content: (
        <div className='space-y-6'>
          {/* Professional Header */}
          <div className='bg-gradient-to-r from-gray-50 to-gray-50 rounded-xl p-6 border border-gray-200'>
            <div className='flex items-center gap-4'>
              <div className='w-12 h-12 bg-gradient-to-br from-gray-700 to-gray-600 rounded-xl flex items-center justify-center shadow-lg'>
                <Globe className='h-6 w-6 text-white' />
              </div>
              <div>
                <h3 className='text-2xl font-bold text-gray-900'>
                  {t('settings.system_integrations')}
                </h3>
                <p className='text-gray-600 font-medium'>
                  {t('settings.connect_external_services')}
                </p>
              </div>
            </div>
          </div>

          {/* Integration Categories */}
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            {/* API Integrations */}
            <div className='bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden'>
              <div className='px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-50'>
                <h4 className='text-lg font-semibold text-gray-900'>
                  {t('settings.api_integrations')}
                </h4>
                <p className='text-sm text-gray-600'>{t('settings.connect_external_data_sources')}</p>
              </div>
              <div className='p-6 space-y-4'>
                <div className='p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center'>
                        <TrendingUp className='h-5 w-5 text-gray-600' />
                      </div>
                      <div>
                        <h5 className='font-semibold text-gray-900 text-sm'>
                          {t('settings.exchange_rate_apis')}
                        </h5>
                        <p className='text-xs text-gray-500'>
                          {t('settings.realtime_currency_conversion')}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-2'>
                      <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                        {t('settings.active')}
                      </span>
                      <button className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-xs font-medium'>
                        {t('settings.configure')}
                      </button>
                    </div>
                  </div>
                </div>

                <div className='p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center'>
                        <Building className='h-5 w-5 text-slate-700' />
                      </div>
                      <div>
                        <h5 className='font-semibold text-gray-900 text-sm'>
                          {t('settings.banking_apis')}
                        </h5>
                        <p className='text-xs text-gray-500'>
                          {t('settings.account_balance_sync')}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-2'>
                      <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800'>
                        {t('settings.pending')}
                      </span>
                      <button className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-xs font-medium'>
                        {t('settings.setup')}
                      </button>
                    </div>
                  </div>
                </div>

                <div className='p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center'>
                        <BarChart3 className='h-5 w-5 text-slate-700' />
                      </div>
                      <div>
                        <h5 className='font-semibold text-gray-900 text-sm'>
                          {t('settings.market_data_apis')}
                        </h5>
                        <p className='text-xs text-gray-500'>
                          {t('settings.stock_prices_analytics')}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-2'>
                      <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600'>
                        {t('settings.inactive')}
                      </span>
                      <button className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-xs font-medium'>
                        {t('settings.enable')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Data Integrations */}
            <div className='bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden'>
              <div className='px-6 py-4 border-b border-gray-200 bg-gray-50'>
                <h4 className='text-lg font-semibold text-gray-900'>
                  {t('settings.data_integrations')}
                </h4>
                <p className='text-sm text-gray-600'>{t('settings.import_export_external_data')}</p>
              </div>
              <div className='p-6 space-y-4'>
                <div className='p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center'>
                        <FileText className='h-5 w-5 text-slate-700' />
                      </div>
                      <div>
                        <h5 className='font-semibold text-gray-900 text-sm'>
                          {t('settings.excel_csv_import')}
                        </h5>
                        <p className='text-xs text-gray-500'>
                          {t('settings.bulk_transaction_import')}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-2'>
                      <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                        {t('settings.active')}
                      </span>
                      <button className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-xs font-medium'>
                        {t('settings.manage')}
                      </button>
                    </div>
                  </div>
                </div>

                <div className='p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center'>
                        <RefreshCw className='h-5 w-5 text-slate-700' />
                      </div>
                      <div>
                        <h5 className='font-semibold text-gray-900 text-sm'>
                          {t('settings.database_sync')}
                        </h5>
                        <p className='text-xs text-gray-500'>
                          {t('settings.realtime_data_sync')}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-2'>
                      <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                        {t('settings.active')}
                      </span>
                      <button className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-xs font-medium'>
                        {t('settings.monitor')}
                      </button>
                    </div>
                  </div>
                </div>

                <div className='p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center'>
                        <Download className='h-5 w-5 text-red-600' />
                      </div>
                      <div>
                        <h5 className='font-semibold text-gray-900 text-sm'>
                          {t('settings.report_export')}
                        </h5>
                        <p className='text-xs text-gray-500'>
                          {t('settings.automated_report_generation')}
                        </p>
                      </div>
                    </div>
                    <div className='flex items-center gap-2'>
                      <span className='inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700'>
                        {t('settings.active')}
                      </span>
                      <button className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-xs font-medium'>
                        {t('settings.configure')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Integration Status Overview */}
          <div className='bg-white rounded-xl shadow-sm border border-gray-200 p-6'>
            <h4 className='text-lg font-semibold text-gray-900 mb-4'>
              {t('settings.integration_health_status')}
            </h4>
            <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
              <div className='text-center p-4 bg-gray-50 rounded-lg border border-slate-200'>
                <div className='w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-2'>
                  <CheckCircle className='h-5 w-5 text-slate-700' />
                </div>
                <p className='text-sm font-medium text-slate-700'>{t('settings.active')}</p>
                <p className='text-xs text-slate-700'>4 {t('settings.integrations')}</p>
              </div>

              <div className='text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200'>
                <div className='w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-2'>
                  <Clock className='h-5 w-5 text-yellow-600' />
                </div>
                <p className='text-sm font-medium text-yellow-800'>{t('settings.pending')}</p>
                <p className='text-xs text-yellow-600'>1 {t('settings.integrations')}</p>
              </div>

              <div className='text-center p-4 bg-gray-50 rounded-lg border border-gray-200'>
                <div className='w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-2'>
                  <Circle className='h-5 w-5 text-gray-600' />
                </div>
                <p className='text-sm font-medium text-gray-800'>{t('settings.inactive')}</p>
                <p className='text-xs text-gray-600'>1 {t('settings.integrations')}</p>
              </div>

              <div className='text-center p-4 bg-gray-50 rounded-lg border border-gray-200'>
                <div className='w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-2'>
                  <BarChart3 className='h-5 w-5 text-gray-600' />
                </div>
                <p className='text-sm font-medium text-gray-800'>{t('settings.total')}</p>
                <p className='text-xs text-gray-600'>6 {t('settings.integrations')}</p>
              </div>
            </div>
          </div>

          {/* Integration Actions */}
          <div className='bg-gradient-to-r from-gray-50 to-gray-50 rounded-xl p-6 border border-gray-200'>
            <div className='flex items-center justify-between'>
              <div>
                <h4 className='text-lg font-semibold text-gray-900 mb-2'>
                  {t('settings.need_more_integrations')}
                </h4>
                <p className='text-sm text-gray-600'>
                  {t('settings.contact_integration_team')}
                </p>
              </div>
              <div className='flex items-center gap-3'>
                <button className='px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 font-medium text-sm'>
                  {t('settings.view_documentation')}
                </button>
                <button className='px-6 py-2 bg-gradient-to-r from-gray-700 to-gray-600 text-white rounded-lg hover:from-gray-800 hover:to-gray-700 transition-all duration-200 font-medium text-sm'>
                  {t('settings.request_integration')}
                </button>
              </div>
            </div>
          </div>
        </div>
      ),
    },
  ];

  return (
    <EnhancedErrorBoundary>
      <div className="p-6">

      {/* Page Header with Tabs */}
      <div className="mb-6">
        <SectionHeader
          title={t('settings.title')}
          description={t('settings.config')}
          icon={SettingsIcon}
          actions={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (activeTab === 'dropdowns') {
                  fetchDropdownOptions();
                } else if (activeTab === 'departments') {
                  fetchDepartments();
                }
              }}
              className="border-gray-300 hover:bg-gray-50"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {t('settings.refresh')}
            </Button>
          }
        />
      </div>

      {/* Tab Navigation */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-5 bg-gray-50/80 border border-gray-200/60 rounded-lg shadow-sm">
          <TabsTrigger value="general" className="flex items-center gap-2">
            <SettingsIcon className="h-4 w-4" />
            {t('tabs.general')}
          </TabsTrigger>
          <TabsTrigger value="dropdowns" className="flex items-center gap-2">
            <List className="h-4 w-4" />
            {t('tabs.dropdowns')}
          </TabsTrigger>
          <TabsTrigger value="departments" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            {t('tabs.departments')}
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            {t('tabs.notifications')}
          </TabsTrigger>
          <TabsTrigger value="integrations" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            {t('tabs.integrations')}
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        {tabs.map(tab => (
          <TabsContent key={tab.id} value={tab.id} className="mt-6">
            {tab.content}
          </TabsContent>
        ))}
      </Tabs>

      {/* Add Option Modal */}
      {showAddModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4' onClick={() => setShowAddModal(false)}>
          <div className="bg-white rounded-xl max-w-md w-full relative" onClick={(e) => e.stopPropagation()}>
            <div className="p-5 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {t('settings.add_option')}
                </h3>
                <UnifiedButton
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddModal(false)}
                  icon={<X className="h-4 w-4" />}
                >
                  {t('common.close')}
                </UnifiedButton>
              </div>
            </div>
            <div className="p-5 space-y-4">
              {/* Custom Dropdown for Field Type */}
              <div className="relative custom-dropdown-container">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('settings.field_type')}
                </label>
                <div className="relative custom-dropdown-container">
                  <button
                    type="button"
                    onClick={() => setIsFieldTypeDropdownOpen(!isFieldTypeDropdownOpen)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white text-gray-900 cursor-pointer text-left flex items-center justify-between hover:border-gray-400 transition-colors"
                  >
                    <span className={formData.field_name ? 'text-gray-900' : 'text-gray-500'}>
                      {formData.field_name 
                        ? fieldTypes.find(f => f.value === formData.field_name)?.label 
                        : t('settings.select_field_type')}
                    </span>
                    <ChevronDown className={`h-4 w-4 text-gray-500 transition-transform ${isFieldTypeDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {/* Dropdown Options */}
                  {isFieldTypeDropdownOpen && (
                    <div className="absolute z-[10001] w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
                      <div className="py-1">
                        {fieldTypes.filter(field => !field.isStatic).map(field => (
                          <button
                            key={field.value}
                            type="button"
                            onClick={() => {
                              setFormData(prev => ({ ...prev, field_name: field.value }));
                              setIsFieldTypeDropdownOpen(false);
                            }}
                            className={`w-full px-3 py-2 text-left hover:bg-gray-100 transition-colors flex items-center justify-between ${
                              formData.field_name === field.value ? 'bg-gray-50 text-gray-900 font-medium' : 'text-gray-700'
                            }`}
                          >
                            <span>{field.label}</span>
                            {formData.field_name === field.value && (
                              <Check className="h-4 w-4 text-gray-600" />
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('settings.option_value')}
                </label>
                <Input
                  type='text'
                  value={formData.value}
                  onChange={e =>
                    setFormData(prev => ({ ...prev, value: e.target.value }))
                  }
                  placeholder={t('settings.enter_option_value')}
                />
              </div>
              {fieldTypes.find(f => f.value === formData.field_name)
                ?.requiresCommission && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('settings.commission_rate_required')}
                    </label>
                    <Input
                      type='number'
                      step='0.01'
                      min='0'
                      max='100'
                      value={formData.commission_rate}
                      onChange={e =>
                        setFormData(prev => ({
                          ...prev,
                          commission_rate: e.target.value,
                        }))
                      }
                      placeholder={t('settings.enter_commission_placeholder')}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {t('settings.commission_help')}
                    </p>
                  </div>
                )}
              {fieldTypes.find(f => f.value === formData.field_name)
                ?.isProtected && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('settings.security_code')} <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="password"
                      value={securityCode}
                      onChange={e => setSecurityCode(e.target.value)}
                      placeholder={t('settings.enter_security_code')}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {t('settings.security_code_required_info')}
                    </p>
                  </div>
                )}
            </div>
            <div className='p-5 border-t border-gray-100 flex gap-3'>
              <UnifiedButton
                variant="outline"
                onClick={() => setShowAddModal(false)}
                className="flex-1"
              >
                {t('common.cancel')}
              </UnifiedButton>
              <UnifiedButton
                variant="primary"
                onClick={handleAddOption}
                disabled={
                  !formData.field_name ||
                  !formData.value ||
                  (fieldTypes.find(f => f.value === formData.field_name)
                    ?.requiresCommission &&
                    !formData.commission_rate) ||
                  (fieldTypes.find(f => f.value === formData.field_name)
                    ?.isProtected &&
                    !securityCode)
                }
                className="flex-1"
              >
                {t('settings.add_option')}
              </UnifiedButton>
            </div>
          </div>
        </div>
      )}

      {/* Edit Option Modal */}
      {showEditModal && editingOption && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4' onClick={() => setShowEditModal(false)}>
          <div className="bg-white rounded-xl max-w-md w-full relative" onClick={(e) => e.stopPropagation()}>
            <div className="p-5 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {t('settings.edit_option')}
                </h3>
                <UnifiedButton
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowEditModal(false)}
                  icon={<X className="h-4 w-4" />}
                >
                  {t('common.close')}
                </UnifiedButton>
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('settings.field_type')}
                </label>
                <Input
                  type="text"
                  value={
                    fieldTypes.find(f => f.value === formData.field_name)
                      ?.label || formData.field_name
                  }
                  className="bg-gray-50"
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('settings.option_value')}
                </label>
                <Input
                  type="text"
                  value={formData.value}
                  onChange={e =>
                    setFormData(prev => ({ ...prev, value: e.target.value }))
                  }
                  placeholder={t('settings.enter_option_value')}
                />
              </div>
              {fieldTypes.find(f => f.value === formData.field_name)
                ?.requiresCommission && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('settings.commission_rate_required')}
                    </label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      max="100"
                      value={formData.commission_rate}
                      onChange={e =>
                        setFormData(prev => ({
                          ...prev,
                          commission_rate: e.target.value,
                        }))
                      }
                      placeholder={t('settings.enter_commission_placeholder')}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {t('settings.commission_help')}
                    </p>
                  </div>
                )}
              {fieldTypes.find(f => f.value === formData.field_name)
                ?.isProtected && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('settings.security_code')} <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="password"
                      value={securityCode}
                      onChange={e => setSecurityCode(e.target.value)}
                      placeholder={t('settings.enter_security_code')}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {t('settings.security_code_edit_info')}
                    </p>
                  </div>
                )}
            </div>
            <div className="p-5 border-t border-gray-100 flex gap-3">
              <UnifiedButton
                variant="outline"
                onClick={() => setShowEditModal(false)}
                className="flex-1"
              >
                {t('common.cancel')}
              </UnifiedButton>
              <UnifiedButton
                variant="primary"
                onClick={handleEditOption}
                disabled={
                  !formData.value ||
                  (fieldTypes.find(f => f.value === formData.field_name)
                    ?.requiresCommission &&
                    !formData.commission_rate) ||
                  (fieldTypes.find(f => f.value === formData.field_name)
                    ?.isProtected &&
                    !securityCode)
                }
                className="flex-1"
              >
                {t('settings.edit_option')}
              </UnifiedButton>
            </div>
          </div>
        </div>
      )}

      {/* Department Modal */}
      {showDepartmentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setShowDepartmentModal(false)}>
          <div className="bg-white rounded-xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="p-5 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {isEditingDepartment ? t('settings.edit_department') : t('settings.add_new_department')}
                </h3>
                <UnifiedButton
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDepartmentModal(false)}
                  icon={<X className="h-4 w-4" />}
                >
                  {t('settings.close')}
                </UnifiedButton>
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('settings.department_name')}
                </label>
                <Input
                  type="text"
                  value={isEditingDepartment ? editingDepartment : newDepartment}
                  onChange={e =>
                    isEditingDepartment
                      ? setEditingDepartment(e.target.value)
                      : setNewDepartment(e.target.value)
                  }
                  placeholder={t('settings.enter_department_name')}
                  autoFocus
                />
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 bg-gray-100 rounded-full flex items-center justify-center mt-0.5">
                    <span className="text-gray-600 text-xs font-bold">i</span>
                  </div>
                  <div className="text-sm text-gray-800">
                    <p className="font-medium mb-1">{t('settings.department_management')}</p>
                    <p className="text-xs">
                      {isEditingDepartment
                        ? t('settings.edit_department_info')
                        : t('settings.add_department_info')
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-5 border-t border-gray-100 flex gap-3">
              <UnifiedButton
                variant="outline"
                onClick={() => setShowDepartmentModal(false)}
                className="flex-1"
              >
                {t('common.cancel')}
              </UnifiedButton>
              <UnifiedButton
                variant="primary"
                onClick={isEditingDepartment ? handleEditDepartment : handleAddDepartment}
                disabled={
                  isEditingDepartment
                    ? !editingDepartment.trim()
                    : !newDepartment.trim()
                }
                className="flex-1"
              >
                {isEditingDepartment ? t('settings.update_department') : t('settings.add_department')}
              </UnifiedButton>
            </div>
          </div>
        </div>
      )}
      </div>
    </EnhancedErrorBoundary>
  );
}
