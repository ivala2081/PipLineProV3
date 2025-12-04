import { ReactNode, useState, useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

interface NotificationProps {
  type: NotificationType
  title: string
  message?: string
  duration?: number
  onClose: () => void
  action?: {
    label: string
    onClick: () => void
  }
}

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info
}

const colors = {
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  warning: 'bg-amber-50 border-amber-200 text-amber-800',
  info: 'bg-gray-50 border-gray-200 text-gray-800'
}

export function Notification({ 
  type, 
  title, 
  message, 
  duration = 5000, 
  onClose, 
  action 
}: NotificationProps) {
  const [isVisible, setIsVisible] = useState(false)
  const Icon = icons[type]

  useEffect(() => {
    setIsVisible(true)
    
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(onClose, 300) // Wait for animation
      }, duration)
      
      return () => clearTimeout(timer)
    }
    return undefined
  }, [duration, onClose])

  return (
    <div
      className={cn(
        "fixed top-4 right-4 z-50 max-w-sm rounded-lg border p-4 shadow-lg transition-all duration-300",
        colors[type],
        isVisible 
          ? "translate-x-0 opacity-100" 
          : "translate-x-full opacity-0"
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm">{title}</h4>
          {message && (
            <p className="mt-1 text-sm opacity-90">{message}</p>
          )}
          {action && (
            <button
              onClick={action.onClick}
              className="mt-2 text-sm font-medium underline hover:no-underline"
            >
              {action.label}
            </button>
          )}
        </div>
        
        <button
          onClick={() => {
            setIsVisible(false)
            setTimeout(onClose, 300)
          }}
          className="flex-shrink-0 text-current opacity-60 hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

// Notification context and hook
interface NotificationContextType {
  showNotification: (notification: Omit<NotificationProps, 'onClose'>) => void
}

export function useNotification() {
  const [notifications, setNotifications] = useState<NotificationProps[]>([])

  const showNotification = (notification: Omit<NotificationProps, 'onClose'>) => {
    const id = Date.now().toString()
    const newNotification: NotificationProps = {
      ...notification,
      onClose: () => {
        setNotifications(prev => prev.filter(n => n !== newNotification))
      }
    }
    
    setNotifications(prev => [...prev, newNotification])
  }

  return {
    notifications,
    showNotification
  }
}
