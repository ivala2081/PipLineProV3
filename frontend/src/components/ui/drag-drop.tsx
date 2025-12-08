import { ReactNode, useState, useRef, DragEvent } from 'react'
import { Upload, File, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DragDropProps {
  onDrop: (files: File[]) => void
  accept?: string
  maxFiles?: number
  maxSize?: number // in MB
  className?: string
  children?: ReactNode
}

export function DragDrop({ 
  onDrop, 
  accept, 
  maxFiles = 10, 
  maxSize = 10,
  className,
  children 
}: DragDropProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [dragCounter, setDragCounter] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragCounter(prev => prev + 1)
    setIsDragOver(true)
  }

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragCounter(prev => prev - 1)
    if (dragCounter === 1) {
      setIsDragOver(false)
    }
  }

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    setDragCounter(0)

    const files = Array.from(e.dataTransfer.files)
    const validFiles = files.filter(file => {
      if (accept && !file.type.match(accept)) return false
      if (file.size > maxSize * 1024 * 1024) return false
      return true
    })

    if (validFiles.length > maxFiles) {
      alert(`Maximum ${maxFiles} files allowed`)
      return
    }

    onDrop(validFiles)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    onDrop(files)
  }

  const openFileDialog = () => {
    fileInputRef.current?.click()
  }

  return (
    <div
      className={cn(
        "relative rounded-lg border-2 border-dashed transition-colors",
        isDragOver 
          ? "border-slate-400 bg-slate-50" 
          : "border-slate-300 hover:border-slate-400",
        className
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={accept}
        onChange={handleFileInput}
        className="hidden"
      />
      
      {children || (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <Upload className="h-12 w-12 text-slate-400 mb-4" />
          <p className="text-lg font-medium text-slate-900 mb-2">
            Drop files here
          </p>
          <p className="text-sm text-slate-500 mb-4">
            or{' '}
            <button
              onClick={openFileDialog}
              className="text-slate-600 hover:text-slate-800 underline"
            >
              browse files
            </button>
          </p>
          <p className="text-xs text-slate-400">
            Max {maxFiles} files, {maxSize}MB each
          </p>
        </div>
      )}
    </div>
  )
}

interface FilePreviewProps {
  file: File
  onRemove: () => void
  className?: string
}

export function FilePreview({ file, onRemove, className }: FilePreviewProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className={cn(
      "flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3",
      className
    )}>
      <File className="h-8 w-8 text-slate-400" />
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 truncate">
          {file.name}
        </p>
        <p className="text-xs text-slate-500">
          {formatFileSize(file.size)}
        </p>
      </div>
      
      <button
        onClick={onRemove}
        className="text-slate-400 hover:text-slate-600 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
