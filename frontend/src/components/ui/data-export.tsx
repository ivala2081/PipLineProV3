import { useState } from 'react'
import { Download, FileText, FileSpreadsheet, FileImage } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ExportOption {
  id: string
  label: string
  icon: React.ReactNode
  format: 'csv' | 'xlsx' | 'pdf' | 'json'
  description: string
}

interface DataExportProps {
  data: any[]
  filename?: string
  onExport: (format: string) => void
  className?: string
}

const exportOptions: ExportOption[] = [
  {
    id: 'csv',
    label: 'CSV',
    icon: <FileText className="h-4 w-4" />,
    format: 'csv',
    description: 'Comma-separated values'
  },
  {
    id: 'xlsx',
    label: 'Excel',
    icon: <FileSpreadsheet className="h-4 w-4" />,
    format: 'xlsx',
    description: 'Microsoft Excel format'
  },
  {
    id: 'pdf',
    label: 'PDF',
    icon: <FileImage className="h-4 w-4" />,
    format: 'pdf',
    description: 'Portable Document Format'
  },
  {
    id: 'json',
    label: 'JSON',
    icon: <FileText className="h-4 w-4" />,
    format: 'json',
    description: 'JavaScript Object Notation'
  }
]

export function DataExport({ data, filename = 'export', onExport, className }: DataExportProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleExport = (format: string) => {
    onExport(format)
    setIsOpen(false)
  }

  return (
    <div className={cn("relative", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
      >
        <Download className="h-4 w-4" />
        Export
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-lg border border-slate-200 bg-white shadow-lg">
            <div className="p-2">
              <div className="px-3 py-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                Export Format
              </div>
              {exportOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => handleExport(option.format)}
                  className="w-full flex items-center gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-slate-50 transition-colors"
                >
                  <div className="text-slate-400">
                    {option.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-slate-900">{option.label}</div>
                    <div className="text-xs text-slate-500">{option.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// Utility functions for different export formats
export const exportUtils = {
  csv: (data: any[], filename: string) => {
    if (data.length === 0) return
    
    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.csv`
    link.click()
    URL.revokeObjectURL(url)
  },

  json: (data: any[], filename: string) => {
    const jsonContent = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.json`
    link.click()
    URL.revokeObjectURL(url)
  },

  pdf: (data: any[], filename: string) => {
    // This would require a PDF library like jsPDF
    console.log('PDF export not implemented yet', { data, filename })
  },

  xlsx: (data: any[], filename: string) => {
    // This would require a library like xlsx
    console.log('Excel export not implemented yet', { data, filename })
  }
}
