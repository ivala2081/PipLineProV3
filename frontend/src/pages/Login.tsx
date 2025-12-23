import React, { useState, useEffect, useRef } from 'react';
import { 
  Input, 
  Label, 
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Checkbox
} from '../components/ui';
import { UnifiedCard, UnifiedButton } from '../design-system';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Banknote, 
  Eye, 
  EyeOff, 
  Shield, 
  AlertTriangle, 
  Lock,
  User,
  Globe,
  KeyRound,
  Smartphone,
  Settings,
  Clock,
  CheckCircle,
  Info,
  Loader2,
  Server,
  Wifi,
  WifiOff
} from 'lucide-react';

interface FormErrors {
  username?: string
  password?: string
  general?: string
}

interface LoginAttempt {
  timestamp: Date
  success: boolean
  ip?: string
}

export default function Login() {
  // Form state
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})

  // Security & validation state
  const [failedAttempts, setFailedAttempts] = useState(0)
  const [isLocked, setIsLocked] = useState(false)
  const [lockoutTime, setLockoutTime] = useState<Date | null>(null)
  const [remainingTime, setRemainingTime] = useState(0)
  const [showCapsLockWarning, setShowCapsLockWarning] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [lastActivity, setLastActivity] = useState<Date>(new Date())

  // UI state
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [systemStatus, setSystemStatus] = useState<'operational' | 'maintenance' | 'issues'>('operational')

  // Refs
  const usernameRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const loginAttemptsRef = useRef<LoginAttempt[]>([])

  // Contexts
  const { login, isAuthenticated } = useAuth();
  const { t, currentLanguage, setLanguage } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  // Password strength calculation
  const calculatePasswordStrength = (pass: string): number => {
    let strength = 0
    if (pass.length >= 6) strength += 25
    if (/[A-Z]/.test(pass)) strength += 25
    if (/[0-9]/.test(pass)) strength += 25
    if (/[^A-Za-z0-9]/.test(pass)) strength += 25
    return strength
  }

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!username.trim()) {
      newErrors.username = t('login.usernameRequired')
    } else if (username.length < 3) {
      newErrors.username = t('login.usernameMinLength')
    }

    if (!password) {
      newErrors.password = t('login.passwordRequired')
    } else if (password.length < 5) {
      newErrors.password = t('login.passwordMinLength')
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Auto-fill remembered username
  useEffect(() => {
    const rememberedUser = localStorage.getItem('pipeline_remember_user')
    if (rememberedUser) {
      setUsername(rememberedUser)
      setRememberMe(true)
    }
  }, [])

  // Handle lockout timer
  useEffect(() => {
    if (!isLocked || !lockoutTime) return

    const interval = setInterval(() => {
      const now = Date.now()
      const remaining = Math.max(0, Math.ceil((lockoutTime.getTime() - now) / 1000))
      
      setRemainingTime(remaining)
      
      if (remaining <= 0) {
        setIsLocked(false)
        setLockoutTime(null)
        setFailedAttempts(0)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [isLocked, lockoutTime, t])

  // Update current time
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
      setLastActivity(new Date())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Focus management
  useEffect(() => {
    if (usernameRef.current) {
      usernameRef.current.focus()
    }
  }, [])

  const getPasswordStrengthColor = (strength: number) => {
    if (strength < 25) return 'bg-red-500'
    if (strength < 50) return 'bg-orange-500'
    if (strength < 75) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getPasswordStrengthText = (strength: number) => {
    if (strength < 25) return t('login.passwordWeak')
    if (strength < 50) return t('login.passwordFair')
    if (strength < 75) return t('login.passwordGood')
    return t('login.passwordStrong')
  }

  // Handle login attempt
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // TEMPORARILY DISABLED - Frontend lockout check
    // if (isLocked) {
    //   toast.error(t('login.accountLocked'), {
    //     description: t('login.accountLockedDesc', { time: Math.ceil(remainingTime / 60) })
    //   })
    //   return
    // }

    if (!validateForm()) {
      return
    }

    setErrors({})
    setIsLoading(true)

    try {
      const startTime = Date.now()
      const result = await login(username, password, rememberMe)
      
      // Record login attempt
      const attempt: LoginAttempt = {
        timestamp: new Date(),
        success: result.success,
        ip: '192.168.1.100' // Mock IP
      }
      loginAttemptsRef.current.push(attempt)

      if (result.success) {
        // Store remember me preference
        if (rememberMe) {
          localStorage.setItem('pipeline_remember_user', username)
        } else {
          localStorage.removeItem('pipeline_remember_user')
        }

        setFailedAttempts(0)
        
        // Login basarili oldugunda dashboard'a yonlendir
        const from = location.state?.from?.pathname || '/dashboard'
        navigate(from, { replace: true })
      } else {
        throw new Error(result.message || t('login.invalidCredentials'))
      }
    } catch (err) {
      const newFailedAttempts = failedAttempts + 1
      setFailedAttempts(newFailedAttempts)

      // TEMPORARILY DISABLED - Frontend lockout after 5 failed attempts
      // if (newFailedAttempts >= 5) {
      //   const lockTime = new Date(Date.now() + 15 * 60 * 1000) // 15 minutes
      //   setIsLocked(true)
      //   setLockoutTime(lockTime)
      //   setRemainingTime(15 * 60)
      //   
      //   toast.error(t('login.accountLocked'), {
      //     description: t('login.tooManyAttempts'),
      //     duration: 5000
      //   })
      // } else {
      if (true) {
        const errorMessage = err instanceof Error ? err.message : t('login.loginFailed')
        setErrors({ general: errorMessage })
      }
    } finally {
      setIsLoading(false)
    }
  }

  // Handle caps lock detection
  const handleKeyPress = (e: React.KeyboardEvent) => {
    const capsLock = e.getModifierState && e.getModifierState('CapsLock')
    setShowCapsLockWarning(capsLock)
  }

  // Handle password change
  const handlePasswordChange = (value: string) => {
    setPassword(value)
    setPasswordStrength(calculatePasswordStrength(value))
  }

  // Handle caps lock detection on key down
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.getModifierState) {
      const capsLock = e.getModifierState('CapsLock')
      setShowCapsLockWarning(capsLock)
    }
  }

return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb', padding: '1rem', position: 'relative' }} className="min-h-screen flex items-center justify-center bg-gray-50 p-4 relative">
      
      {/* Network Status Indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2 bg-card border rounded-lg px-3 py-2 shadow-sm">
        {isOnline ? (
          <Wifi className="w-4 h-4 text-green-500" />
        ) : (
          <WifiOff className="w-4 h-4 text-red-500" />
        )}
        <span className="text-xs text-muted-foreground">
          {isOnline ? t('login.online') : t('login.offline')}
        </span>
      </div>

      {/* System Status */}
      <div className="absolute top-4 left-4 flex items-center gap-2 bg-card border rounded-lg px-3 py-2 shadow-sm">
        <Server className={`w-4 h-4 ${systemStatus === 'operational' ? 'text-green-500' : systemStatus === 'maintenance' ? 'text-yellow-500' : 'text-red-500'}`} />
        <span className="text-xs text-muted-foreground">
          {systemStatus === 'operational' && t('login.systemOperational')}
          {systemStatus === 'maintenance' && t('login.systemMaintenance')}
          {systemStatus === 'issues' && t('login.systemIssues')}
        </span>
      </div>

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Header */}
        <div className="text-center space-y-4">
          {/* Logo */}
          <div className="mx-auto flex items-center justify-center">
            <img 
              src="/plogo.png" 
              alt="PipLinePro Logo" 
              className="w-24 h-24 object-contain"
            />
          </div>
          
          {/* Branding */}
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">PipLinePro</h1>
            <p className="text-muted-foreground">{t('login.systemTitle')}</p>
          </div>

          {/* Time & Date Display */}
          <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{currentTime.toLocaleTimeString(currentLanguage === 'tr' ? 'tr-TR' : 'en-US')}</span>
            </div>
            <div className="w-px h-4 bg-border" />
            <span>{currentTime.toLocaleDateString(currentLanguage === 'tr' ? 'tr-TR' : 'en-US')}</span>
          </div>
        </div>

        {/* Quick Settings */}
        <div className="flex items-center justify-center gap-2">
          {/* Language Selector */}
          <Select value={currentLanguage} onValueChange={setLanguage}>
            <SelectTrigger className="w-auto border-0 bg-transparent hover:bg-muted/50 transition-colors">
              <Globe className="w-4 h-4 mr-1" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="tr">Türkçe</SelectItem>
            </SelectContent>
          </Select>

        </div>

        {/* Account Lockout Warning */}
        {isLocked && (
          <Alert variant="destructive">
            <Lock className="h-4 w-4" />
            <AlertDescription>
              {t('login.accountLockedMessage', { 
                minutes: Math.ceil(remainingTime / 60),
                seconds: remainingTime % 60 
              })}
            </AlertDescription>
          </Alert>
        )}

        {/* Network Status Warning */}
        {!isOnline && (
          <Alert className="border-orange-200 bg-orange-50">
            <WifiOff className="h-4 w-4 text-orange-600" />
            <AlertDescription className="text-orange-800">
              {t('login.offlineMode')}
            </AlertDescription>
          </Alert>
        )}

        {/* Login Form */}
        <UnifiedCard 
          variant="elevated"
          size="md"
          padding="lg"
          className="shadow-md bg-white"
          header={{
            title: (
              <span className="flex items-center gap-2">
                <KeyRound className="w-5 h-5" />
                {t('login.signIn')}
              </span>
            ),
            description: t('login.signInDescription')
          }}
        >
          <div className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* General Error */}
              {errors.general && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{errors.general}</AlertDescription>
                </Alert>
              )}

              {/* Username Field */}
              <div className="space-y-2">
                <Label htmlFor="username" className="flex items-center gap-1">
                  <User className="w-4 h-4" />
                  {t('login.username')}
                  <span className="text-destructive">*</span>
                </Label>
                <Input
                  ref={usernameRef}
                  id="username"
                  type="text"
                  placeholder={t('login.usernamePlaceholder')}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading || isLocked}
                  className={`bg-input-background transition-all ${
                    errors.username ? 'border-destructive focus-visible:ring-destructive' : ''
                  }`}
                  autoComplete="username"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && passwordRef.current) {
                      passwordRef.current.focus()
                    }
                  }}
                />
                {errors.username && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {errors.username}
                  </p>
                )}
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password" className="flex items-center gap-1">
                  <Lock className="w-4 h-4" />
                  {t('login.password')}
                  <span className="text-destructive">*</span>
                </Label>
                <div className="relative">
                  <Input
                    ref={passwordRef}
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder={t('login.passwordPlaceholder')}
                    value={password}
                    onChange={(e) => handlePasswordChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading || isLocked}
                    className={`bg-input-background pr-10 transition-all ${
                      errors.password ? 'border-destructive focus-visible:ring-destructive' : ''
                    }`}
                    autoComplete="current-password"
                  />
                  <UnifiedButton
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isLoading || isLocked}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </UnifiedButton>
                </div>

                {/* Password Strength Indicator */}
                {password && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        {t('login.passwordStrength')}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {getPasswordStrengthText(passwordStrength)}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-300 ${getPasswordStrengthColor(passwordStrength)}`}
                        style={{ width: `${passwordStrength}%` }}
                      />
                    </div>
                  </div>
                )}

                {errors.password && (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {errors.password}
                  </p>
                )}

                {/* Caps Lock Warning */}
                {showCapsLockWarning && (
                  <p className="text-sm text-orange-600 flex items-center gap-1">
                    <Info className="w-3 h-3" />
                    {t('login.capsLockOn')}
                  </p>
                )}
              </div>

              {/* Remember Me & Failed Attempts */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="remember"
                    checked={rememberMe}
                    onCheckedChange={(checked) => setRememberMe(checked === true)}
                    disabled={isLoading || isLocked}
                  />
                  <Label
                    htmlFor="remember"
                    className="text-sm cursor-pointer text-muted-foreground"
                  >
                    {t('login.rememberMe')}
                  </Label>
                </div>
                {failedAttempts > 0 && (
                  <span className="text-xs text-orange-600">
                    {t('login.failedAttempts', { count: failedAttempts })}
                  </span>
                )}
              </div>

              {/* Advanced Options Toggle */}
              <UnifiedButton
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                className="w-full text-muted-foreground hover:text-foreground"
                icon={<Settings className="w-4 h-4" />}
                iconPosition="left"
              >
                {showAdvancedOptions ? t('login.hideAdvanced') : t('login.showAdvanced')}
              </UnifiedButton>

              {/* Advanced Options */}
              {showAdvancedOptions && (
                <div className="p-3 bg-muted/30 rounded-lg space-y-3 border">
                  <div className="text-sm font-medium text-muted-foreground">
                    {t('login.advancedOptions')}
                  </div>
                  
                  {/* Two-Factor Authentication Placeholder */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Smartphone className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">{t('login.twoFactorAuth')}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{t('login.notConfigured')}</span>
                  </div>

                  {/* Session Duration */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">{t('login.sessionDuration')}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">8 {t('login.hours')}</span>
                  </div>
                </div>
              )}

              {/* Login Button */}
              <UnifiedButton 
                type="submit" 
                variant="primary"
                size="lg"
                className="w-full" 
                disabled={isLoading || isLocked || !username || !password || !isOnline}
                loading={isLoading}
                icon={isLoading ? undefined : <KeyRound className="w-4 h-4" />}
                iconPosition="left"
              >
                {isLoading ? t('login.signingIn') : t('login.signIn')}
              </UnifiedButton>
            </form>

{/* Recent Login Attempts */}
            {loginAttemptsRef.current.length > 0 && (
              <div className="mt-6 p-4 bg-muted/30 rounded-lg border border-border/50">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-muted-foreground" />
                  <p className="text-sm font-medium text-muted-foreground">
                    {t('login.recentActivity')}
                  </p>
                </div>
                <div className="space-y-1">
                  {loginAttemptsRef.current.slice(-3).map((attempt, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        {attempt.success ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <AlertTriangle className="w-3 h-3 text-red-500" />
                        )}
                        <span className="text-muted-foreground">
                          {attempt.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <span className={attempt.success ? 'text-green-600' : 'text-red-600'}>
                        {attempt.success ? t('login.success') : t('login.failed')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </UnifiedCard>

        {/* Footer */}
        <div className="text-center space-y-2 text-xs text-muted-foreground">
          <p>© 2024 PipLinePro {t('login.allRightsReserved')}</p>
          <p>{t('login.secureTreasuryManagement')}</p>
          <p className="flex items-center justify-center gap-1">
            <Shield className="w-3 h-3" />
            {t('login.encryptedConnection')}
          </p>
        </div>
      </div>
    </div>
  )
}
