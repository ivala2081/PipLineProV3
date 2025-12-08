import { useState, useCallback } from 'react'

interface LoadingState {
  isLoading: boolean
  error: string | null
  data: any
}

export function useLoadingState<T = any>(initialData: T = null as T) {
  const [state, setState] = useState<LoadingState>({
    isLoading: false,
    error: null,
    data: initialData
  })

  const setLoading = useCallback((isLoading: boolean) => {
    setState(prev => ({ ...prev, isLoading, error: isLoading ? null : prev.error }))
  }, [])

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, isLoading: false }))
  }, [])

  const setData = useCallback((data: T) => {
    setState(prev => ({ ...prev, data, isLoading: false, error: null }))
  }, [])

  const reset = useCallback(() => {
    setState({ isLoading: false, error: null, data: initialData })
  }, [initialData])

  return {
    ...state,
    setLoading,
    setError,
    setData,
    reset
  }
}
