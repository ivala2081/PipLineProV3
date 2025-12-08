import { useEffect, useCallback } from 'react'

interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  metaKey?: boolean
  action: () => void
  description?: string
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const pressedKey = event.key.toLowerCase()
    
    for (const shortcut of shortcuts) {
      const {
        key,
        ctrlKey = false,
        shiftKey = false,
        altKey = false,
        metaKey = false,
        action
      } = shortcut
      
      if (
        pressedKey === key.toLowerCase() &&
        event.ctrlKey === ctrlKey &&
        event.shiftKey === shiftKey &&
        event.altKey === altKey &&
        event.metaKey === metaKey
      ) {
        event.preventDefault()
        action()
        break
      }
    }
  }, [shortcuts])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}

// Common shortcuts
export const COMMON_SHORTCUTS = {
  SAVE: { key: 's', ctrlKey: true, description: 'Save' },
  NEW: { key: 'n', ctrlKey: true, description: 'New' },
  SEARCH: { key: 'k', ctrlKey: true, description: 'Search' },
  REFRESH: { key: 'r', ctrlKey: true, description: 'Refresh' },
  CLOSE: { key: 'Escape', description: 'Close' },
  DELETE: { key: 'Delete', description: 'Delete' },
  EDIT: { key: 'e', ctrlKey: true, description: 'Edit' },
  EXPORT: { key: 'e', ctrlKey: true, shiftKey: true, description: 'Export' }
}
