import { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import {
  FileText,
  Download,
  Calendar,
  TrendingUp,
  BarChart3,
  PieChart,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { 
  UnifiedCard, 
  UnifiedButton, 
  UnifiedBadge, 
  UnifiedSection, 
  UnifiedGrid 
} from '../design-system';
import { Breadcrumb } from '../components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

export default function Reports() {
  const { t } = useLanguage();
  const [selectedReport, setSelectedReport] = useState('financial');

  const reports = [
    {
      id: 'financial',
      name: 'Financial Reports',
      icon: TrendingUp,
      description: 'Revenue, expenses, and profit analysis',
    },
    {
      id: 'transaction',
      name: 'Transaction Reports',
      icon: BarChart3,
      description: 'Detailed transaction analysis and trends',
    },
    {
      id: 'client',
      name: 'Client Reports',
      icon: PieChart,
      description: 'Client performance and activity reports',
    },
    {
      id: 'agent',
      name: 'Agent Reports',
      icon: FileText,
      description: 'Agent performance and productivity reports',
    },
  ];

  return (
    <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <FileText className="h-8 w-8 text-gray-600" />
              Reports
            </h1>
            <p className="text-gray-600">Generate and view comprehensive business reports</p>
          </div>
          <div className="flex items-center gap-3">
            <UnifiedButton 
              variant="outline" 
              size="sm" 
              onClick={() => window.location.reload()}
              icon={<RefreshCw className='h-4 w-4' />}
            >
              Refresh
            </UnifiedButton>
            <UnifiedButton variant="outline" size="sm" icon={<Calendar className='h-4 w-4' />}>
              Date Range
            </UnifiedButton>
            <UnifiedButton variant="outline" size="sm" icon={<Filter className='h-4 w-4' />}>
              Filters
            </UnifiedButton>
            <UnifiedButton variant="primary" size="sm" icon={<Download className='h-4 w-4' />}>
              Export Report
            </UnifiedButton>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">

      {/* Report Types Section */}
      <UnifiedCard variant="elevated" className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-gray-600" />
            Available Reports
          </CardTitle>
          <CardDescription>
            Select the type of report you want to generate
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {reports.map(report => (
              <div
                key={report.id}
                onClick={() => setSelectedReport(report.id)}
                className={`cursor-pointer transition-all duration-200 ${
                  selectedReport === report.id
                    ? 'ring-2 ring-gray-500 bg-gray-50/50'
                    : 'hover:bg-gray-50 hover:shadow-md'
                }`}
              >
                <UnifiedCard
                  variant={selectedReport === report.id ? "elevated" : "outlined"}
                  className="h-full"
                >
                <CardContent className="p-6">
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-lg ${
                      selectedReport === report.id ? 'bg-gray-100' : 'bg-gray-100'
                    }`}>
                      <report.icon className={`h-6 w-6 ${
                        selectedReport === report.id ? 'text-gray-600' : 'text-gray-600'
                      }`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{report.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">{report.description}</p>
                    </div>
                  </div>
                </CardContent>
                </UnifiedCard>
              </div>
            ))}
          </div>
        </CardContent>
      </UnifiedCard>

      {/* Report Content */}
      <UnifiedCard variant="elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {(() => {
              const selectedReportData = reports.find(r => r.id === selectedReport);
              const IconComponent = selectedReportData?.icon;
              return IconComponent ? <IconComponent className="h-5 w-5 text-gray-600" /> : null;
            })()}
            {reports.find(r => r.id === selectedReport)?.name}
          </CardTitle>
          <CardDescription>
            {reports.find(r => r.id === selectedReport)?.description}
          </CardDescription>
        </CardHeader>
        <CardContent>

        <div className='space-y-6'>
          {/* Placeholder content for each report type */}
          {selectedReport === 'financial' && (
            <div className='space-y-4'>
              <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                <div className='p-4 bg-green-50 rounded-lg'>
                  <h4 className='font-medium text-green-900'>
                    {t('dashboard.total_revenue')}
                  </h4>
                  <p className='text-2xl font-bold text-green-600'>
                    $125,000
                  </p>
                </div>
                <div className='p-4 bg-red-50 rounded-lg'>
                  <h4 className='font-medium text-red-900'>Total Expenses</h4>
                  <p className='text-2xl font-bold text-red-600'>$45,000</p>
                </div>
                <div className='p-4 bg-gray-50 rounded-lg'>
                  <h4 className='font-medium text-gray-900'>Net Profit</h4>
                  <p className='text-2xl font-bold text-gray-600'>$80,000</p>
                </div>
              </div>
              <div className='h-64 bg-gray-100 rounded-lg flex items-center justify-center'>
                <p className='text-gray-500'>
                  Financial charts and graphs will be displayed here
                </p>
              </div>
            </div>
          )}

          {selectedReport === 'transaction' && (
            <div className='space-y-4'>
              <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                <div className='p-4 bg-gray-50 rounded-lg'>
                  <h4 className='font-medium text-gray-900'>
                    {t('dashboard.total_transactions')}
                  </h4>
                  <p className='text-2xl font-bold text-gray-600'>1,234</p>
                </div>
                <div className='p-4 bg-green-50 rounded-lg'>
                  <h4 className='font-medium text-green-900'>Successful</h4>
                  <p className='text-2xl font-bold text-green-600'>1,180</p>
                </div>
                <div className='p-4 bg-yellow-50 rounded-lg'>
                  <h4 className='font-medium text-yellow-900'>Pending</h4>
                  <p className='text-2xl font-bold text-yellow-600'>54</p>
                </div>
              </div>
              <div className='h-64 bg-gray-100 rounded-lg flex items-center justify-center'>
                <p className='text-gray-500'>
                  Transaction charts and graphs will be displayed here
                </p>
              </div>
            </div>
          )}

          {selectedReport === 'client' && (
            <div className='space-y-4'>
              <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                <div className='p-4 bg-purple-50 rounded-lg'>
                  <h4 className='font-medium text-purple-900'>
                    Total Clients
                  </h4>
                  <p className='text-2xl font-bold text-purple-600'>156</p>
                </div>
                <div className='p-4 bg-green-50 rounded-lg'>
                  <h4 className='font-medium text-green-900'>
                    {t('dashboard.active_clients')}
                  </h4>
                  <p className='text-2xl font-bold text-green-600'>142</p>
                </div>
                <div className='p-4 bg-gray-50 rounded-lg'>
                  <h4 className='font-medium text-gray-900'>
                    New This Month
                  </h4>
                  <p className='text-2xl font-bold text-gray-600'>12</p>
                </div>
              </div>
              <div className='h-64 bg-gray-100 rounded-lg flex items-center justify-center'>
                <p className='text-gray-500'>
                  Client analytics charts will be displayed here
                </p>
              </div>
            </div>
          )}

          {selectedReport === 'agent' && (
            <div className='space-y-4'>
              <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                <div className='p-4 bg-indigo-50 rounded-lg'>
                  <h4 className='font-medium text-indigo-900'>
                    Total Agents
                  </h4>
                  <p className='text-2xl font-bold text-indigo-600'>24</p>
                </div>
                <div className='p-4 bg-green-50 rounded-lg'>
                  <h4 className='font-medium text-green-900'>
                    Active Agents
                  </h4>
                  <p className='text-2xl font-bold text-green-600'>22</p>
                </div>
                <div className='p-4 bg-yellow-50 rounded-lg'>
                  <h4 className='font-medium text-yellow-900'>
                    Avg. Performance
                  </h4>
                  <p className='text-2xl font-bold text-yellow-600'>87%</p>
                </div>
              </div>
              <div className='h-64 bg-gray-100 rounded-lg flex items-center justify-center'>
                <p className='text-gray-500'>
                  Agent performance charts will be displayed here
                </p>
              </div>
            </div>
          )}
        </div>
        </CardContent>
      </UnifiedCard>
      </div>
    </div>
  );
}
