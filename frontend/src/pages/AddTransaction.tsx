import { useState, useEffect } from 'react';
import {
  Plus,
  X,
  User,
  Calendar,
  DollarSign,
  Building2,
  CreditCard,
  Building,
  Tag,
  MessageSquare,
  ArrowLeft,
  Settings,
  AlertTriangle,
  CheckCircle,
  Info,
  FileText,
  Globe,
  TrendingUp,
  Save,
  RefreshCw,
  Shield,
  Clock,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../utils/apiClient';
import { exchangeRatesService } from '../services/exchangeRatesService';
import { healthMonitor } from '../services/healthMonitor';
import CurrencyConversionModal from '../components/CurrencyConversionModal';
import { UnifiedButton } from '../design-system/UnifiedComponent';
import { UnifiedCard } from '../design-system/UnifiedComponent';

interface DropdownOption {
  id: number;
  value: string;
  commission_rate?: number;
}

interface GroupedOptions {
  [fieldName: string]: DropdownOption[];
}

interface ExchangeRate {
  eur_rate?: number;
  has_rates: boolean;
}

export default function AddTransaction() {
  const { t } = useLanguage();
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [dropdownOptions, setDropdownOptions] = useState<GroupedOptions>({});
  const [dropdownsLoaded, setDropdownsLoaded] = useState(false);
  
  // Fallback static options if API fails
  const staticFallbackOptions: GroupedOptions = {
    currency: [
      { id: 1, value: 'TL' },
      { id: 2, value: 'USD' },
      { id: 3, value: 'EUR' }
    ],
    payment_method: [
      { id: 1, value: 'Bank' },
      { id: 2, value: 'Credit card' },
      { id: 3, value: 'Tether' }
    ],
    psp: [],
    company: []
  };
  const [exchangeRate, setExchangeRate] = useState<ExchangeRate>({
    has_rates: false,
  });
  const [showExchangeRateSection, setShowExchangeRateSection] = useState(false);
  const [showCurrencyModal, setShowCurrencyModal] = useState(false);
  const [rateValidationMessage, setRateValidationMessage] = useState('');
  const [convertedAmountTL, setConvertedAmountTL] = useState<string>('');
  const [autoSaveStatus, setAutoSaveStatus] = useState<'saved' | 'saving' | 'error'>('saved');
  
  // Manual commission state
  const [showManualCommission, setShowManualCommission] = useState(false);
  const [securityCode, setSecurityCode] = useState('');
  const [manualCommission, setManualCommission] = useState('');
  const [securityCodeVerified, setSecurityCodeVerified] = useState(false);
  const [securityCodeError, setSecurityCodeError] = useState('');

  const [formData, setFormData] = useState({
    client_name: '',
    company: '',
    date: '',
    amount: '',
    payment_method: '',
    currency: '',
    category: '',
    psp: '',
    notes: '',
    eur_rate: '',
    usd_rate: '',
  });

  // Auto-save functionality
  const AUTO_SAVE_KEY = 'addTransaction_autoSave';
  const AUTO_SAVE_DELAY = 2000; // 2 seconds delay

  // Load saved form data on component mount
  useEffect(() => {
    const savedData = localStorage.getItem(AUTO_SAVE_KEY);
    if (savedData) {
      try {
        const parsedData = JSON.parse(savedData);
        setFormData(parsedData);
        console.log('📁 Auto-saved form data restored');
      } catch (error) {
        console.error('❌ Error parsing saved form data:', error);
        localStorage.removeItem(AUTO_SAVE_KEY);
      }
    }
  }, []);

  // Auto-save form data when it changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      // Only save if form has meaningful data
      if (formData.client_name || formData.amount || formData.date) {
        setAutoSaveStatus('saving');
        try {
          localStorage.setItem(AUTO_SAVE_KEY, JSON.stringify(formData));
          setAutoSaveStatus('saved');
          console.log('💾 Form data auto-saved');
        } catch (error) {
          console.error('❌ Auto-save failed:', error);
          setAutoSaveStatus('error');
        }
      }
    }, AUTO_SAVE_DELAY);

    return () => clearTimeout(timeoutId);
  }, [formData]);

  useEffect(() => {
    // Only fetch dropdowns if we're authenticated and they haven't been loaded yet
    if (isAuthenticated && !authLoading && !dropdownsLoaded) {
      fetchDropdownOptions();

      // Perform health check when component mounts
      healthMonitor.performHealthCheck().then(result => {
        if (result.issues.length > 0) {
          console.warn('⚠️ Health issues detected:', result.issues);
        }
      });
    }
  }, [isAuthenticated, authLoading, dropdownsLoaded]);

  // Fallback: If dropdowns still aren't loaded after a delay, try again
  useEffect(() => {
    if (isAuthenticated && !authLoading && !dropdownsLoaded) {
      const timeoutId = setTimeout(() => {
        if (!dropdownsLoaded) {
          fetchDropdownOptions();
        }
      }, 1000); // Wait 1 second before retry

      return () => clearTimeout(timeoutId);
    }
    return undefined;
  }, [isAuthenticated, authLoading, dropdownsLoaded]);

  const fetchDropdownOptions = async () => {
    try {
      setLoading(true);
      setError(null); // Clear previous errors
      
      const response = await api.get<GroupedOptions>('/transactions/dropdown-options');

      if (response.ok && response.data) {
        // API direkt olarak {currency: [...], payment_method: [...], ...} formatında döndürüyor
        const data = response.data as GroupedOptions;
        console.log('✅ Dropdown options loaded successfully:', data);
        console.log('📊 Dropdown data structure:', {
          currency: data.currency,
          payment_method: data.payment_method,
          psp: data.psp,
          company: data.company,
        });
        
        // Validate data structure
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid data format received from API');
        }
        
        setDropdownOptions(data);
        setDropdownsLoaded(true);
      } else {
        const errorMsg = `API returned status ${response.status}`;
        console.error('Failed to fetch dropdown options:', errorMsg);
        setError(`Dropdown seçenekleri yüklenemedi (Status: ${response.status}). Lütfen sayfayı yenileyin.`);
      }
    } catch (error: any) {
      console.error('Error fetching dropdown options:', error);
      const errorMessage = error?.message || 'Bilinmeyen hata';
      const errorDetails = error?.status ? ` (Status: ${error.status})` : '';
      
      // Use fallback static options instead of showing error
      console.warn('⚠️ Using fallback static options due to API error');
      setDropdownOptions(staticFallbackOptions);
      setDropdownsLoaded(true);
      
      // Show warning instead of error
      setError(`Dropdown seçenekleri API'den yüklenemedi, varsayılan değerler kullanılıyor. (${errorMessage}${errorDetails})`);
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setError(null);
      }, 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Show currency modal when USD is selected
    if (field === 'currency' && value === 'USD') {
      setShowCurrencyModal(true);
    }

    // Check exchange rates when currency or date changes
    if (field === 'currency' || field === 'date') {
      // Pass the new values to checkExchangeRates
      const newFormData = { ...formData, [field]: value };
      checkExchangeRates(newFormData.currency, newFormData.date);
    }
  };

  const handleCurrencyRateSelect = (rate: number) => {
    setFormData(prev => ({ ...prev, usd_rate: rate.toString() }));
    setShowCurrencyModal(false);
  };

  const checkExchangeRates = async (currency?: string, date?: string) => {
    // Use passed parameters or fall back to current formData
    const currentCurrency = currency || formData.currency;
    const currentDate = date || formData.date;

    if ((currentCurrency === 'EUR' || currentCurrency === 'USD') && currentDate) {
      setShowExchangeRateSection(true);
      await validateExistingRates(currentDate, currentCurrency);
    } else {
      setShowExchangeRateSection(false);
    }
  };

  const validateExistingRates = async (date: string, currency: string) => {
    try {
      setRateValidationMessage('Checking existing rates...');

      if (currency === 'EUR') {
        const res = await exchangeRatesService.fetchRate({ date, currency_pair: 'EUR/TRY' });
        if (res.status === 'success' && res.rate?.rate) {
          const r = res.rate.rate;
          setRateValidationMessage(`✓ EUR/TRY rate fetched: ${r}`);
          setExchangeRate({ has_rates: true, eur_rate: r });
          setFormData(prev => ({ ...prev, eur_rate: r.toString() }));
        } else {
          setRateValidationMessage(`⚠ EUR/TRY rate not found for ${date}.`);
          setExchangeRate({ has_rates: false });
          setFormData(prev => ({ ...prev, eur_rate: '0.00' }));
        }
      }

      if (currency === 'USD') {
        const res = await exchangeRatesService.fetchRate({ date, currency_pair: 'USD/TRY' });
        if (res.status === 'success' && res.rate?.rate) {
          const r = res.rate.rate;
          setRateValidationMessage(`✓ USD/TRY rate fetched: ${r}`);
          setFormData(prev => ({ ...prev, usd_rate: r.toString() }));
        } else {
          setRateValidationMessage(`⚠ USD/TRY rate not found for ${date}.`);
          setFormData(prev => ({ ...prev, usd_rate: '0.00' }));
        }
      }
    } catch (error) {
      setRateValidationMessage(`✗ Error: ${error}`);
    }
  };

  const applyUsdRate = () => {
    const amount = parseFloat(formData.amount || '0');
    const rate = parseFloat(formData.usd_rate || '0');
    if (!isNaN(amount) && !isNaN(rate) && rate > 0) {
      const tl = amount * rate;
      setConvertedAmountTL(tl.toFixed(2));
    } else {
      setConvertedAmountTL('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    console.log('🚀 Starting transaction creation...', {
      formData,
      timestamp: new Date().toISOString(),
    });

    // Enhanced validation
    if (!formData.client_name.trim()) {
      setError('Client name is required.');
      return;
    }

    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      setError('Please enter a valid amount greater than 0.');
      return;
    }

    if (!formData.date) {
      setError('Please select a date.');
      return;
    }

    if (!formData.currency) {
      setError('Please select a currency.');
      return;
    }

    if (!formData.category) {
      setError('Please select a category (WD or DEP).');
      return;
    }

    // Validate category is one of the allowed values
    if (!['WD', 'DEP'].includes(formData.category)) {
      setError('Category must be WD (Withdraw) or DEP (Deposit).');
      return;
    }

    // Validate currency is one of the allowed values
    if (!['TL', 'USD', 'EUR'].includes(formData.currency)) {
      setError('Currency must be TL, USD, or EUR.');
      return;
    }

    if (formData.currency === 'EUR' && !formData.eur_rate) {
      setError('Please enter the EUR exchange rate.');
      return;
    }

    if (formData.currency === 'USD' && !formData.usd_rate) {
      setError('Please enter the USD exchange rate.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      // Pre-submission session validation with enhanced checks
      console.log('🔍 Validating session before transaction submission...');

      // Step 1: Check if we have a valid session
      const authResponse = await api.get('/auth/check');
      if (!authResponse.ok) {
        console.warn('⚠️ Auth check failed, attempting session refresh...');
        const sessionValid = await api.refreshSession();
        if (!sessionValid) {
          setError(
            'Session validation failed. Please refresh the page and try again.'
          );
          setSubmitting(false);
          return;
        }
      }

      // Step 2: Ensure we have a fresh CSRF token
      const csrfResponse = await api.get('/auth/csrf-token');
      if (!csrfResponse.ok) {
        console.warn(
          '⚠️ CSRF token check failed, attempting session refresh...'
        );
        const sessionValid = await api.refreshSession();
        if (!sessionValid) {
          setError(
            'CSRF token validation failed. Please refresh the page and try again.'
          );
          setSubmitting(false);
          return;
        }
      }

      // Prepare payload with exchange rate if provided
      const payload: any = { ...formData };
      if (formData.currency === 'USD' && formData.usd_rate) {
        payload.exchange_rate = formData.usd_rate;
      }
      if (formData.currency === 'EUR' && formData.eur_rate) {
        payload.exchange_rate = formData.eur_rate;
      }
      
      // Add manual commission if enabled and provided
      if (securityCodeVerified && manualCommission && parseFloat(manualCommission) > 0) {
        payload.manual_commission_rate = parseFloat(manualCommission);
        payload.use_manual_commission = true;
      }

      // Try to create transaction with automatic retry
      let response: any = null;
      let retryCount = 0;
      const maxRetries = 2;

      while (retryCount <= maxRetries) {
        try {
          response = await api.post('/transactions/', payload);

          // If successful, break out of retry loop
          if (response && response.ok) {
            break;
          }

          // Log error details from backend
          if (response && !response.ok && response.data) {
            const errorData: any = response.data;
            console.error('❌ Backend Error:', {
              status: response.status,
              error: errorData.error,
              message: errorData.message || errorData.error?.message,
              fullData: errorData,
            });
          }

          // If we get a 401 or 400, try to refresh session and retry
          if (
            response && (response.status === 401 || response.status === 400) &&
            retryCount < maxRetries
          ) {
            console.log(
              `🔄 Attempt ${retryCount + 1}: Session/CSRF issue detected, refreshing...`
            );

            // Force refresh session with multiple methods
            try {
              // Method 1: Direct API refresh
              const refreshSuccess = await api.refreshSession();
              if (!refreshSuccess) {
                console.warn(
                  'Direct API refresh failed, trying health monitor...'
                );
                // Method 2: Health monitor refresh
                await healthMonitor.refreshSession();
              }
            } catch (refreshError) {
              console.warn('All refresh methods failed:', refreshError);
              // Method 3: Manual page refresh as last resort
              if (retryCount === maxRetries - 1) {
                console.log('🔄 Last resort: suggesting page refresh...');
                setError(
                  'Session expired. Please refresh the page and try again.'
                );
                setSubmitting(false);
                return;
              }
            }

            retryCount++;
            continue;
          }

          // For other errors, break and handle normally
          break;
        } catch (error) {
          console.error(`💥 Attempt ${retryCount + 1} failed:`, error);

          if (retryCount < maxRetries) {
            console.log(`🔄 Retrying... (${retryCount + 1}/${maxRetries})`);
            retryCount++;
            // Wait a bit before retrying
            await new Promise(resolve => setTimeout(resolve, 1000));
            continue;
          } else {
            throw error;
          }
        }
      }

      // Ensure we have a response
      if (!response) {
        throw new Error(
          'Failed to get response from server after all retry attempts'
        );
      }

      console.log('📥 Received API response:', {
        status: response.status,
        ok: response.ok,
        hasData: !!response.data,
        data: response.data,
      });

      // If response is not ok, try to get error message from response
      if (!response.ok) {
        let errorMessage = 'Failed to add transaction';
        try {
          const errorData: any = response.data;
          if (errorData?.error?.message) {
            errorMessage = errorData.error.message;
          } else if (errorData?.error) {
            errorMessage = typeof errorData.error === 'string' ? errorData.error : JSON.stringify(errorData.error);
          } else if (errorData?.message) {
            errorMessage = errorData.message;
          } else if (typeof errorData === 'string') {
            errorMessage = errorData;
          }
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
        }
        
        console.error('❌ API Error Response:', {
          status: response.status,
          message: errorMessage,
          data: response.data,
        });
        
        throw new Error(`Server error (${response.status}): ${errorMessage}`);
      }

      const data: any = api.parseResponse(response);

      console.log('🔍 Parsed response data:', data);

      // Handle both new standardized format and legacy format
      const isSuccess = response.ok && (
        (data && typeof data === 'object' && 'success' in data && data.success) || 
        (data && typeof data === 'object' && 'id' in data) ||
        (data && typeof data === 'object' && 'transaction' in data)
      );

      if (isSuccess) {
        console.log('✅ Transaction created successfully!');
        setSuccess(true);
        
        // Clear auto-saved data
        localStorage.removeItem(AUTO_SAVE_KEY);
        setAutoSaveStatus('saved');
        
        // Get transaction ID from various formats
        const transactionId = 
          (data as any)?.transaction?.id || 
          (data as any)?.id || 
          (data as any)?.data?.id;
        
        // Dispatch event to refresh transaction lists in other components
        // Add a small delay to ensure transaction is fully committed
        setTimeout(() => {
          console.log('🔄 Dispatching transactionsUpdated event...');
          window.dispatchEvent(new CustomEvent('transactionsUpdated', {
            detail: { 
              action: 'create',
              transactionId: transactionId
            }
          }));
        }, 500);
        
        // Reset form
        setFormData({
          client_name: '',
          company: '',
          date: '',
          amount: '',
          payment_method: '',
          currency: '',
          category: '',
          psp: '',
          notes: '',
          eur_rate: '',
          usd_rate: '',
        });
        setConvertedAmountTL('');
      } else {
        const errorMessage =
          (data as any)?.error?.message ||
          (data as any)?.error ||
          (data as any)?.message ||
          'Failed to add transaction';
        console.error('❌ Transaction creation failed:', errorMessage);
        setError(errorMessage);
      }
    } catch (error) {
      console.error('💥 Error adding transaction:', error);

      // Enhanced error handling
      if (error instanceof Error) {
        const errorMessage = error.message;
        console.error('Error details:', {
          message: errorMessage,
          stack: error.stack,
          timestamp: new Date().toISOString(),
        });

        // Provide more specific error messages
        if (
          errorMessage.includes('CSRF') ||
          errorMessage.includes('Security token')
        ) {
          setError(
            'Security token issue. Please refresh the page and try again.'
          );
        } else if (
          errorMessage.includes('Authentication') ||
          errorMessage.includes('login')
        ) {
          setError('Session expired. Please log in again.');
        } else if (
          errorMessage.includes('401') ||
          errorMessage.includes('unauthorized')
        ) {
          setError('Authentication required. Please log in to continue.');
        } else if (
          errorMessage.includes('308') ||
          errorMessage.includes('redirect')
        ) {
          setError('URL redirect issue. Please try again.');
        } else if (errorMessage.includes('404')) {
          setError('API endpoint not found. Please check your connection.');
        } else if (errorMessage.includes('500')) {
          setError('Server error. Please try again in a few moments.');
        } else if (errorMessage.includes('403')) {
          setError('Access denied. Please check your permissions.');
        } else {
          setError(`Failed to add transaction: ${errorMessage}`);
        }
      } else {
        setError('Failed to add transaction. Please try again.');
      }
    } finally {
      setSubmitting(false);
      console.log('🏁 Transaction creation process completed');
    }
  };

  const handleCancel = () => {
    // Navigate back to transactions page
    window.location.href = '/clients';
  };

  const handleSecurityCodeVerification = () => {
    if (securityCode === '4561') {
      setSecurityCodeVerified(true);
      setSecurityCodeError('');
      setShowManualCommission(true);
    } else {
      setSecurityCodeError('Invalid security code. Please try again.');
      setSecurityCodeVerified(false);
    }
  };

  const handleManualCommissionToggle = () => {
    if (!securityCodeVerified) {
      setShowManualCommission(false);
      setSecurityCode('');
      setSecurityCodeError('');
    }
  };

  const resetForm = () => {
    setFormData({
      client_name: '',
      company: '',
      date: '',
      amount: '',
      payment_method: '',
      currency: '',
      category: '',
      psp: '',
      notes: '',
      eur_rate: '',
      usd_rate: '',
    });
    setSuccess(false);
    setError(null);
    setDropdownsLoaded(false);
    setConvertedAmountTL('');
    
    // Clear auto-saved data
    localStorage.removeItem(AUTO_SAVE_KEY);
    setAutoSaveStatus('saved');
  };

  // Loading state
  if (authLoading || loading) {
    return (
      <div className='min-h-screen bg-gray-50 flex items-center justify-center p-4'>
        <UnifiedCard className="max-w-sm w-full text-center" variant="elevated">
          <div className='space-y-4'>
            <div className='w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto'>
              <RefreshCw className='h-8 w-8 text-blue-600 animate-spin' />
            </div>
            <div>
              <h2 className='text-xl font-semibold text-gray-900 mb-2'>
                Loading Transaction Form
              </h2>
              <p className='text-gray-600'>
                Please wait while we prepare the form and load your options...
              </p>
            </div>
          </div>
        </UnifiedCard>
      </div>
    );
  }

  if (success) {
    return (
      <div className='min-h-screen bg-gray-50 flex items-center justify-center p-4'>
        <UnifiedCard className="max-w-md w-full text-center" variant="elevated">
          <div className='space-y-6'>
            <div className='w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto'>
              <CheckCircle className='h-10 w-10 text-green-600' />
            </div>
            <div>
              <h2 className='text-2xl font-bold text-gray-900 mb-2'>
                Transaction Added Successfully!
              </h2>
              <p className='text-gray-600'>
                The transaction has been added to your pipeline and is now available in your transaction list.
              </p>
            </div>
            <div className='flex flex-col sm:flex-row gap-3'>
              <UnifiedButton
                variant="primary"
                size="lg"
                onClick={() => (window.location.href = '/clients')}
                icon={<FileText className="h-4 w-4" />}
                className="flex-1"
              >
                View Clients
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="lg"
                onClick={resetForm}
                icon={<Plus className="h-4 w-4" />}
                className="flex-1"
              >
                Add Another
              </UnifiedButton>
            </div>
          </div>
        </UnifiedCard>
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gray-50'>
      {/* Professional Header */}
      <div className='bg-white border-b border-gray-200 shadow-sm'>
        <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
          <div className='flex items-center justify-between h-16'>
            <div className='flex items-center space-x-4'>
              <UnifiedButton
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                icon={<ArrowLeft className="h-4 w-4" />}
                className="text-gray-600 hover:text-gray-900"
              >
                Back to Transactions
              </UnifiedButton>
              <div className='h-6 w-px bg-gray-300' />
              <div className='flex items-center space-x-3'>
                <div className='w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center shadow-sm'>
                  <FileText className='h-5 w-5 text-white' />
                </div>
                <div>
                  <h1 className='text-xl font-semibold text-gray-900'>
                    Add New Transaction
                  </h1>
                  <p className='text-sm text-gray-500'>
                    Create a new transaction record
                  </p>
                </div>
              </div>
            </div>
            <div className='flex items-center space-x-3'>
              <div className='flex items-center space-x-2 text-sm'>
                {autoSaveStatus === 'saving' && (
                  <>
                    <RefreshCw className='h-4 w-4 text-blue-500 animate-spin' />
                    <span className='text-blue-600'>Saving...</span>
                  </>
                )}
                {autoSaveStatus === 'saved' && (
                  <>
                    <CheckCircle className='h-4 w-4 text-green-500' />
                    <span className='text-green-600'>Auto-saved</span>
                  </>
                )}
                {autoSaveStatus === 'error' && (
                  <>
                    <AlertTriangle className='h-4 w-4 text-red-500' />
                    <span className='text-red-600'>Save failed</span>
                  </>
                )}
              </div>
              <div className='flex items-center space-x-2 text-sm text-green-600'>
                <Shield className='h-4 w-4' />
                <span>Secure</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className='max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8'>
        <div className='space-y-6'>

          {/* Error Message */}
          {error && (
            <UnifiedCard
              variant="outlined"
              className="border-red-200 bg-red-50"
            >
              <div className='flex items-center gap-3'>
                <div className='w-8 h-8 bg-red-100 rounded-full flex items-center justify-center'>
                  <AlertTriangle className='h-4 w-4 text-red-600' />
                </div>
                <div>
                  <h3 className='font-medium text-red-900'>Validation Error</h3>
                  <p className='text-sm text-red-700 mt-1'>{error}</p>
                </div>
              </div>
            </UnifiedCard>
          )}

          {/* Main Form */}
          <form onSubmit={handleSubmit} className='space-y-6'>
            {/* Basic Information Card */}
            <UnifiedCard
              header={{
                title: "Basic Information",
                description: "Essential transaction details"
              }}
            >
              <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    Client Name *
                  </label>
                  <div className='relative'>
                    <User className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                    <input
                      type='text'
                      value={formData.client_name}
                      onChange={e => handleInputChange('client_name', e.target.value)}
                      className='w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white'
                      placeholder='Enter client name'
                      required
                    />
                  </div>
                </div>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    Transaction Date *
                  </label>
                  <div className='relative'>
                    <Calendar className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                    <input
                      type='date'
                      value={formData.date}
                      onChange={e => handleInputChange('date', e.target.value)}
                      className='w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white'
                      required
                    />
                  </div>
                </div>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    Amount *
                  </label>
                  <div className='relative'>
                    <DollarSign className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                    <input
                      type='number'
                      step='0.01'
                      value={formData.amount}
                      onChange={e => handleInputChange('amount', e.target.value)}
                      className='w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white'
                      placeholder='0.00'
                      required
                    />
                  </div>
                </div>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    Currency *
                  </label>
                  <div className='relative'>
                    <Globe className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none z-10' />
                    <select
                      value={formData.currency}
                      onChange={e => handleInputChange('currency', e.target.value)}
                      className='w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white appearance-none cursor-pointer'
                      required
                      disabled={!dropdownsLoaded}
                    >
                      <option value=''>{dropdownsLoaded ? 'Select Currency' : 'Loading...'}</option>
                      {dropdownOptions.currency && dropdownOptions.currency.length > 0 ? (
                        dropdownOptions.currency.map(option => (
                          <option key={option.id} value={option.value}>
                            {option.value}
                          </option>
                        ))
                      ) : dropdownsLoaded ? (
                        // Fallback options if API doesn't return data
                        [
                          <option key='TL' value='TL'>TL</option>,
                          <option key='USD' value='USD'>USD</option>,
                          <option key='EUR' value='EUR'>EUR</option>
                        ]
                      ) : null}
                    </select>
                    <div className='absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none'>
                      <svg className='h-4 w-4 text-gray-400' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </UnifiedCard>

            {/* Payment Information Card */}
            <UnifiedCard
              header={{
                title: "Payment Information",
                description: "Payment method and transaction category"
              }}
            >
              <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    Payment Method *
                  </label>
                  <div className='relative'>
                    <CreditCard className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none z-10' />
                    <select
                      value={formData.payment_method}
                      onChange={e => handleInputChange('payment_method', e.target.value)}
                      className='w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white appearance-none cursor-pointer'
                      required
                      disabled={!dropdownsLoaded}
                    >
                      <option value=''>{dropdownsLoaded ? 'Select Payment Method' : 'Loading...'}</option>
                      {dropdownOptions.payment_method && dropdownOptions.payment_method.length > 0 ? (
                        dropdownOptions.payment_method.map(option => (
                          <option key={option.id} value={option.value}>
                            {option.value}
                          </option>
                        ))
                      ) : dropdownsLoaded ? (
                        // Fallback options if API doesn't return data
                        [
                          <option key='Bank' value='Bank'>Bank</option>,
                          <option key='CreditCard' value='Credit card'>Credit card</option>,
                          <option key='Tether' value='Tether'>Tether</option>
                        ]
                      ) : null}
                    </select>
                    <div className='absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none'>
                      <svg className='h-4 w-4 text-gray-400' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                      </svg>
                    </div>
                  </div>
                </div>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    Transaction Category *
                  </label>
                  <div className='relative'>
                    <Tag className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none z-10' />
                    <select
                      value={formData.category}
                      onChange={e => handleInputChange('category', e.target.value)}
                      className='w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white appearance-none cursor-pointer'
                      required
                    >
                      <option value=''>Select Category</option>
                      <option value='WD'>WD (Withdraw)</option>
                      <option value='DEP'>DEP (Deposit)</option>
                    </select>
                    <div className='absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none'>
                      <svg className='h-4 w-4 text-gray-400' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                      </svg>
                    </div>
                  </div>
                  <div className='flex items-center gap-2 text-sm text-gray-600 bg-blue-50 p-2 rounded-lg'>
                    <Info className='h-4 w-4 text-blue-500' />
                    <span>WD = Withdraw (no commission), DEP = Deposit (with commission)</span>
                  </div>
                </div>
                <div className='space-y-2'>
                  <label className='block text-sm font-medium text-gray-700'>
                    PSP/KASA (Optional)
                  </label>
                  <div className='relative'>
                    <Building2 className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none z-10' />
                    <select
                      value={formData.psp}
                      onChange={e => handleInputChange('psp', e.target.value)}
                      className='w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white appearance-none cursor-pointer'
                      disabled={!dropdownsLoaded}
                    >
                      <option value=''>{dropdownsLoaded ? 'Select PSP/KASA' : 'Loading...'}</option>
                      {dropdownOptions.psp && dropdownOptions.psp.length > 0 ? (
                        dropdownOptions.psp.map(option => (
                          <option key={option.id} value={option.value}>
                            {option.value}
                          </option>
                        ))
                      ) : null}
                    </select>
                    <div className='absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none'>
                      <svg className='h-4 w-4 text-gray-400' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </UnifiedCard>

            {/* Manual Commission - Minimal Design */}
            <div className='bg-white border border-gray-200 rounded-lg p-4'>
              <div className='flex items-center justify-between mb-3'>
                <h3 className='text-sm font-medium text-gray-900'>Manual Commission</h3>
                {securityCodeVerified && (
                  <span className='inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full'>
                    <CheckCircle className='h-3 w-3' />
                    Active
                  </span>
                )}
              </div>
              
              {!securityCodeVerified ? (
                <div className='space-y-3'>
                  <div className='flex gap-2'>
                    <input
                      type='password'
                      value={securityCode}
                      onChange={e => setSecurityCode(e.target.value)}
                      className='flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                      placeholder='Security code'
                    />
                    <button
                      type='button'
                      onClick={handleSecurityCodeVerification}
                      className='px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:ring-1 focus:ring-blue-500'
                    >
                      Enable
                    </button>
                  </div>
                  {securityCodeError && (
                    <p className='text-xs text-red-600'>{securityCodeError}</p>
                  )}
                </div>
              ) : (
                <div className='space-y-3'>
                  <div className='flex gap-2'>
                    <input
                      type='number'
                      step='0.01'
                      value={manualCommission}
                      onChange={e => setManualCommission(e.target.value)}
                      className='flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500'
                      placeholder='Commission %'
                    />
                    <button
                      type='button'
                      onClick={() => {
                        setSecurityCodeVerified(false);
                        setShowManualCommission(false);
                        setSecurityCode('');
                        setManualCommission('');
                        setSecurityCodeError('');
                      }}
                      className='px-3 py-2 text-sm font-medium text-gray-600 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200'
                    >
                      Disable
                    </button>
                  </div>
                  <p className='text-xs text-gray-500'>Overrides automatic PSP commission rate</p>
                </div>
              )}
            </div>

            {/* Company Information Card */}
            <UnifiedCard
              header={{
                title: "Company Information",
                description: "Select the company for this transaction"
              }}
            >
              <div className='space-y-2'>
                <label className='block text-sm font-medium text-gray-700'>
                  Company
                </label>
                <div className='relative'>
                  <Building className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none z-10' />
                  <select
                    value={formData.company}
                    onChange={e => handleInputChange('company', e.target.value)}
                    className='w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white appearance-none cursor-pointer'
                    disabled={!dropdownsLoaded}
                  >
                    <option value=''>{dropdownsLoaded ? 'Select Company' : 'Loading...'}</option>
                    {dropdownOptions.company && dropdownOptions.company.length > 0 ? (
                      dropdownOptions.company.map(option => (
                        <option key={option.id} value={option.value}>
                          {option.value}
                        </option>
                      ))
                    ) : null}
                  </select>
                  <div className='absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none'>
                    <svg className='h-4 w-4 text-gray-400' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
                    </svg>
                  </div>
                </div>
              </div>
            </UnifiedCard>

            {/* Additional Information Card */}
            <UnifiedCard
              header={{
                title: "Additional Information",
                description: "Optional notes and comments"
              }}
            >
              <div className='space-y-2'>
                <label className='block text-sm font-medium text-gray-700'>
                  Transaction Notes
                </label>
                <div className='relative'>
                  <MessageSquare className='absolute left-3 top-3 h-4 w-4 text-gray-400' />
                  <textarea
                    value={formData.notes}
                    onChange={e => handleInputChange('notes', e.target.value)}
                    className='w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white resize-none'
                    placeholder='Enter any additional notes or comments about this transaction'
                    rows={4}
                  />
                </div>
                <div className='flex items-center gap-2 text-sm text-gray-600 bg-gray-50 p-2 rounded-lg'>
                  <Info className='h-4 w-4 text-gray-500' />
                  <span>Optional notes to help track transaction details</span>
                </div>
              </div>
            </UnifiedCard>

            {/* Exchange Rate Section */}
            {showExchangeRateSection && (
              <UnifiedCard
                variant="outlined"
                className="border-amber-200 bg-amber-50"
                header={{
                  title: "Exchange Rates Required",
                  description: "Foreign currency transactions require exchange rates"
                }}
              >
                <div className='space-y-4'>
                  <div className='flex items-center gap-3 p-4 bg-amber-100 border border-amber-200 rounded-lg'>
                    <AlertTriangle className='h-5 w-5 text-amber-600 flex-shrink-0' />
                    <div>
                      <p className='text-amber-800 font-medium'>
                        Exchange rates are required for foreign currency transactions
                      </p>
                      <p className='text-amber-700 text-sm mt-1'>
                        Please enter the exchange rates for the selected date to ensure accurate conversions
                      </p>
                    </div>
                  </div>

                  <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                    {formData.currency === 'EUR' && (
                      <div className='space-y-2'>
                        <label className='block text-sm font-medium text-gray-700'>
                          EUR to TL Rate
                        </label>
                        <div className='relative'>
                          <TrendingUp className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                          <input
                            type='number'
                            step='0.0001'
                            min='0'
                            value={formData.eur_rate}
                            onChange={e => handleInputChange('eur_rate', e.target.value)}
                            className='w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white'
                            placeholder='0.0000'
                            required={formData.currency === 'EUR'}
                          />
                        </div>
                        <p className='text-sm text-gray-600 bg-gray-50 p-2 rounded-lg'>
                          Auto-fetched when possible. If no rate, it defaults to 0.00.
                        </p>
                      </div>
                    )}

                    {formData.currency === 'USD' && (
                      <div className='space-y-2'>
                        <label className='block text-sm font-medium text-gray-700'>
                          USD to TL Rate
                        </label>
                        <div className='flex gap-2'>
                          <div className='relative flex-1'>
                            <TrendingUp className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                            <input
                              type='number'
                              step='0.0001'
                              min='0'
                              value={formData.usd_rate}
                              onChange={e => handleInputChange('usd_rate', e.target.value)}
                              className='w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-white'
                              placeholder='0.0000'
                            />
                          </div>
                          <UnifiedButton
                            type='button'
                            variant="success"
                            size="sm"
                            onClick={() => setShowCurrencyModal(true)}
                            icon={<DollarSign className="h-4 w-4" />}
                          >
                            Get Rate
                          </UnifiedButton>
                          <UnifiedButton
                            type='button'
                            variant="outline"
                            size="sm"
                            onClick={applyUsdRate}
                            icon={<RefreshCw className="h-4 w-4" />}
                          >
                            Apply
                          </UnifiedButton>
                        </div>
                        {convertedAmountTL && (
                          <div className='p-3 bg-green-50 border border-green-200 rounded-lg'>
                            <p className='text-sm text-green-800'>
                              <strong>Converted TL Amount:</strong> {convertedAmountTL}
                            </p>
                          </div>
                        )}
                        <p className='text-sm text-gray-600 bg-gray-50 p-2 rounded-lg'>
                          Auto-fetched when possible. If no rate, it defaults to 0.00.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Rate Validation Status */}
                  {rateValidationMessage && (
                    <div className='p-4 bg-blue-50 border border-blue-200 rounded-lg'>
                      <div className='flex items-center gap-3'>
                        <Info className='h-5 w-5 text-blue-600 flex-shrink-0' />
                        <div>
                          <p className='text-blue-800 font-medium'>Rate Validation</p>
                          <p className='text-blue-700 text-sm'>{rateValidationMessage}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </UnifiedCard>
            )}

            {/* Form Actions */}
            <UnifiedCard className="bg-gray-50">
              <div className='flex flex-col sm:flex-row gap-3'>
                <UnifiedButton
                  type='button'
                  variant="outline"
                  size="lg"
                  onClick={handleCancel}
                  className="flex-1"
                  icon={<X className="h-4 w-4" />}
                >
                  Cancel
                </UnifiedButton>
                <UnifiedButton
                  type='submit'
                  variant="primary"
                  size="lg"
                  disabled={submitting}
                  loading={submitting}
                  className="flex-1"
                  icon={<Save className="h-4 w-4" />}
                >
                  {submitting ? 'Adding Transaction...' : 'Add Transaction'}
                </UnifiedButton>
              </div>
            </UnifiedCard>
        </form>

        {/* Settings Link */}
        <UnifiedCard
          header={{
            title: "Dropdown Management",
            description: "Customize your dropdown options"
          }}
        >
          <div className='text-center space-y-4'>
            <UnifiedButton
              variant="success"
              size="lg"
              onClick={() => window.location.href = '/settings?tab=dropdowns'}
              icon={<Settings className="h-4 w-4" />}
              className="mx-auto"
            >
              Manage Dropdown Options
            </UnifiedButton>
            <div className='p-4 bg-blue-50 border border-blue-200 rounded-lg'>
              <div className='flex items-start gap-3 text-left'>
                <Info className='h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5' />
                <div className='text-sm'>
                  <p className='font-medium text-blue-900 mb-1'>
                    Need to customize dropdown options?
                  </p>
                  <p className='text-blue-800'>
                    Add your own payment methods, companies, or PSPs by clicking the button above. 
                    This will take you to the settings page where you can manage all dropdown options.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </UnifiedCard>
        </div>
      </div>

      {/* Currency Conversion Modal */}
      <CurrencyConversionModal
        isOpen={showCurrencyModal}
        onClose={() => setShowCurrencyModal(false)}
        onRateSelect={handleCurrencyRateSelect}
        currentAmount={parseFloat(formData.amount) || 0}
        transactionDate={formData.date}
      />
    </div>
  );
}
