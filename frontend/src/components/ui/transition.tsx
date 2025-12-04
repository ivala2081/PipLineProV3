import { ReactNode, useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface TransitionProps {
  children: ReactNode
  show: boolean
  className?: string
  duration?: number
  delay?: number
}

export function Transition({ 
  children, 
  show, 
  className = '',
  duration = 200,
  delay = 0
}: TransitionProps) {
  const [isVisible, setIsVisible] = useState(show)
  const [shouldRender, setShouldRender] = useState(show)

  useEffect(() => {
    if (show) {
      setShouldRender(true)
      const timer = setTimeout(() => setIsVisible(true), delay)
      return () => clearTimeout(timer)
    } else {
      setIsVisible(false)
      const timer = setTimeout(() => setShouldRender(false), duration)
      return () => clearTimeout(timer)
    }
  }, [show, delay, duration])

  if (!shouldRender) return null

  return (
    <div
      className={cn(
        'transition-all duration-200 ease-in-out',
        isVisible 
          ? 'opacity-100 translate-y-0' 
          : 'opacity-0 translate-y-2',
        className
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  )
}
