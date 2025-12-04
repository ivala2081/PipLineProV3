import React from 'react';
import { X, Filter, RefreshCw, Download, ChevronDown } from 'lucide-react';
import { UnifiedCard, UnifiedButton, UnifiedBadge } from '../design-system';
import { CardHeader, CardTitle, CardDescription, CardContent } from './ui/card';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { FormField } from './ui/form-field';
import { useLanguage } from '../contexts/LanguageContext';

interface FilterState {
  search: string;
  category: string;
  psp: string;
  company: string;
  payment_method: string;
  currency: string;
  status: string;
  date_from: string;
  date_to: string;
  amount_min: string;
  amount_max: string;
  commission_min: string;
  commission_max: string;
  client_name: string;
  sort_by: string;
  sort_order: string;
}

interface DropdownOptions {
  psps: string[];
  categories: string[];
  payment_methods: string[];
  currencies: string[];
  companies: string[];
}

interface ExpandedFilterSections {
  basic: boolean;
  advanced: boolean;
  amounts: boolean;
  dates: boolean;
}

interface TransactionFilterPanelProps {
  filters: FilterState;
  dropdownOptions: DropdownOptions;
  expandedFilterSections: ExpandedFilterSections;
  displayLimit: number;
  transactionsLength: number;
  exporting: boolean;
  onFilterChange: (key: string, value: string) => void;
  onToggleFilterSection: (section: keyof ExpandedFilterSections) => void;
  onClearAllFilters: () => void;
  onApplyFilters: () => void;
  onExportDisplayed: () => void;
  onExportAll: () => void;
  onApplyQuickFilter: (filterType: string) => void;
}

export default function TransactionFilterPanel({
  filters,
  dropdownOptions,
  expandedFilterSections,
  displayLimit,
  transactionsLength,
  exporting,
  onFilterChange,
  onToggleFilterSection,
  onClearAllFilters,
  onApplyFilters,
  onExportDisplayed,
  onExportAll,
  onApplyQuickFilter,
}: TransactionFilterPanelProps) {
  const { t } = useLanguage();

  const getActiveFilterCount = () => {
    return Object.values(filters).filter(value => 
      value && value !== 'created_at' && value !== 'desc' && value !== 'all'
    ).length;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <UnifiedCard variant="outlined" className="overflow-hidden border-slate-300 bg-white">
      <CardHeader className="bg-white border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-100 rounded-lg">
              <Filter className="h-5 w-5 text-slate-700" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-slate-900">
                Transaction Filters
              </CardTitle>
              <CardDescription className="text-slate-600">
                Filter and search transactions
                {activeFilterCount > 0 && (
                  <span className="ml-2 px-2 py-0.5 bg-slate-900 text-white text-xs font-medium rounded">
                    {activeFilterCount}
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeFilterCount > 0 && (
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={onClearAllFilters}
                icon={<X className="h-4 w-4" />}
                className="text-slate-700 hover:bg-slate-100 border-slate-300"
              >
                Clear All
              </UnifiedButton>
            )}
            <UnifiedButton
              variant="ghost"
              size="sm"
              onClick={() => {/* Parent controls visibility */}}
              icon={<X className="h-4 w-4" />}
              className="text-slate-600 hover:bg-slate-100"
            >
              Close
            </UnifiedButton>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-6">
          {/* Quick Filters */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-sm font-semibold text-slate-900">Quick Filters</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => onApplyQuickFilter('today')}
                className="bg-white hover:bg-slate-100 border-slate-300 text-slate-700"
              >
                Today
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => onApplyQuickFilter('thisWeek')}
                className="bg-white hover:bg-slate-100 border-slate-300 text-slate-700"
              >
                This Week
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => onApplyQuickFilter('deposits')}
                className="bg-white hover:bg-slate-100 border-slate-300 text-slate-700"
              >
                Deposits
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => onApplyQuickFilter('withdrawals')}
                className="bg-white hover:bg-slate-100 border-slate-300 text-slate-700"
              >
                Withdrawals
              </UnifiedButton>
              <UnifiedButton
                variant="outline"
                size="sm"
                onClick={() => onApplyQuickFilter('highValue')}
                className="bg-white hover:bg-slate-100 border-slate-300 text-slate-700"
              >
                High Value (₺10K+)
              </UnifiedButton>
            </div>
          </div>

          {/* Basic Filters Section */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div 
              className="flex items-center justify-between cursor-pointer bg-slate-50 p-3 hover:bg-slate-100 transition-colors"
              onClick={() => onToggleFilterSection('basic')}
            >
              <div className="flex items-center gap-3">
                <div className={`transition-transform duration-200 ${expandedFilterSections.basic ? 'rotate-180' : ''}`}>
                  <ChevronDown className="h-4 w-4 text-slate-600" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">Basic Filters</h3>
                {(filters.search || (filters.category && filters.category !== 'all') || (filters.status && filters.status !== 'all')) && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-slate-900 text-white">
                    {(filters.search ? 1 : 0) + ((filters.category && filters.category !== 'all') ? 1 : 0) + ((filters.status && filters.status !== 'all') ? 1 : 0)}
                  </UnifiedBadge>
                )}
              </div>
            </div>
            
            {expandedFilterSections.basic && (
              <div className="p-4 bg-white border-t border-slate-200">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <FormField label="Search">
                    <Input
                      placeholder="Search transactions..."
                      variant="default"
                      size="default"
                      value={filters.search}
                      onChange={(e) => onFilterChange('search', e.target.value)}
                    />
                  </FormField>
                  <FormField label="Category">
                    <Select
                      value={filters.category}
                      onValueChange={value => onFilterChange('category', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="All Categories" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Categories</SelectItem>
                        <SelectItem value="DEP">Deposit (DEP)</SelectItem>
                        <SelectItem value="WD">Withdrawal (WD)</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormField>
                  <FormField label="Status">
                    <Select
                      value={filters.status}
                      onValueChange={value => onFilterChange('status', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="All Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormField>
                </div>
              </div>
            )}
          </div>

          {/* Advanced Filters Section */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div 
              className="flex items-center justify-between cursor-pointer bg-slate-50 p-3 hover:bg-slate-100 transition-colors"
              onClick={() => onToggleFilterSection('advanced')}
            >
              <div className="flex items-center gap-3">
                <div className={`transition-transform duration-200 ${expandedFilterSections.advanced ? 'rotate-180' : ''}`}>
                  <ChevronDown className="h-4 w-4 text-slate-600" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">Advanced Filters</h3>
                {((filters.psp && filters.psp !== 'all') || (filters.company && filters.company !== 'all') || (filters.payment_method && filters.payment_method !== 'all') || (filters.currency && filters.currency !== 'all')) && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-slate-900 text-white">
                    {((filters.psp && filters.psp !== 'all') ? 1 : 0) + ((filters.company && filters.company !== 'all') ? 1 : 0) + ((filters.payment_method && filters.payment_method !== 'all') ? 1 : 0) + ((filters.currency && filters.currency !== 'all') ? 1 : 0)}
                  </UnifiedBadge>
                )}
              </div>
            </div>
            
            {expandedFilterSections.advanced && (
              <div className="p-4 bg-white border-t border-slate-200">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <FormField label="PSP">
                    <Select
                      value={filters.psp}
                      onValueChange={value => onFilterChange('psp', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="All PSPs" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All PSPs</SelectItem>
                        {dropdownOptions.psps.map((psp: string) => (
                          <SelectItem key={psp} value={psp}>{psp}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormField>
                  <FormField label="Company">
                    <Select
                      value={filters.company}
                      onValueChange={value => onFilterChange('company', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="All Companies" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Companies</SelectItem>
                        {dropdownOptions.companies.map((company: string) => (
                          <SelectItem key={company} value={company}>{company}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormField>
                  <FormField label="Payment Method">
                    <Select
                      value={filters.payment_method}
                      onValueChange={value => onFilterChange('payment_method', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="All Methods" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Methods</SelectItem>
                        {dropdownOptions.payment_methods.map((method: string) => (
                          <SelectItem key={method} value={method}>{method}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormField>
                  <FormField label="Currency">
                    <Select
                      value={filters.currency}
                      onValueChange={value => onFilterChange('currency', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="All Currencies" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Currencies</SelectItem>
                        {dropdownOptions.currencies.map((currency: string) => (
                          <SelectItem key={currency} value={currency}>{currency}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormField>
                </div>
              </div>
            )}
          </div>

          {/* Amount Filters Section */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div 
              className="flex items-center justify-between cursor-pointer bg-slate-50 p-3 hover:bg-slate-100 transition-colors"
              onClick={() => onToggleFilterSection('amounts')}
            >
              <div className="flex items-center gap-3">
                <div className={`transition-transform duration-200 ${expandedFilterSections.amounts ? 'rotate-180' : ''}`}>
                  <ChevronDown className="h-4 w-4 text-slate-600" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">Amount Filters</h3>
                {(filters.amount_min || filters.amount_max || filters.commission_min || filters.commission_max) && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-slate-900 text-white">
                    {(filters.amount_min ? 1 : 0) + (filters.amount_max ? 1 : 0) + (filters.commission_min ? 1 : 0) + (filters.commission_max ? 1 : 0)}
                  </UnifiedBadge>
                )}
              </div>
            </div>
            
            {expandedFilterSections.amounts && (
              <div className="p-4 bg-white border-t border-slate-200">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      {t('clients.min_amount')}
                    </label>
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={filters.amount_min}
                      onChange={(e) => onFilterChange('amount_min', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      {t('clients.max_amount')}
                    </label>
                    <Input
                      type="number"
                      placeholder="1000000.00"
                      value={filters.amount_max}
                      onChange={(e) => onFilterChange('amount_max', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      {t('clients.min_commission')}
                    </label>
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={filters.commission_min}
                      onChange={(e) => onFilterChange('commission_min', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">
                      {t('clients.max_commission')}
                    </label>
                    <Input
                      type="number"
                      placeholder="10000.00"
                      value={filters.commission_max}
                      onChange={(e) => onFilterChange('commission_max', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Date & Sorting Section */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <div 
              className="flex items-center justify-between cursor-pointer bg-slate-50 p-3 hover:bg-slate-100 transition-colors"
              onClick={() => onToggleFilterSection('dates')}
            >
              <div className="flex items-center gap-3">
                <div className={`transition-transform duration-200 ${expandedFilterSections.dates ? 'rotate-180' : ''}`}>
                  <ChevronDown className="h-4 w-4 text-slate-600" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900">Date & Sorting</h3>
                {(filters.date_from || filters.date_to || filters.sort_by !== 'date' || filters.sort_order !== 'desc') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-slate-900 text-white">
                    {(filters.date_from ? 1 : 0) + (filters.date_to ? 1 : 0) + (filters.sort_by !== 'date' ? 1 : 0) + (filters.sort_order !== 'desc' ? 1 : 0)}
                  </UnifiedBadge>
                )}
              </div>
            </div>
            
            {expandedFilterSections.dates && (
              <div className="p-4 bg-white border-t border-slate-200">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <FormField label="From Date">
                    <Input
                      type="date"
                      variant="default"
                      size="default"
                      value={filters.date_from}
                      onChange={(e) => onFilterChange('date_from', e.target.value)}
                    />
                  </FormField>
                  <FormField label="To Date">
                    <Input
                      type="date"
                      variant="default"
                      size="default"
                      value={filters.date_to}
                      onChange={(e) => onFilterChange('date_to', e.target.value)}
                    />
                  </FormField>
                  <FormField label="Sort By">
                    <Select
                      value={filters.sort_by}
                      onValueChange={value => onFilterChange('sort_by', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="Sort By" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="created_at">Date Created</SelectItem>
                        <SelectItem value="amount">Amount</SelectItem>
                        <SelectItem value="commission">Commission</SelectItem>
                        <SelectItem value="client_name">Client Name</SelectItem>
                        <SelectItem value="psp">PSP</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormField>
                  <FormField label="Sort Order">
                    <Select
                      value={filters.sort_order}
                      onValueChange={value => onFilterChange('sort_order', value)}
                    >
                      <SelectTrigger variant="default" size="default">
                        <SelectValue placeholder="Sort Order" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="desc">Descending</SelectItem>
                        <SelectItem value="asc">Ascending</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormField>
                </div>
              </div>
            )}
          </div>

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <h4 className="text-sm font-semibold text-slate-900">Active Filters</h4>
                <UnifiedBadge variant="secondary" size="sm" className="bg-slate-900 text-white">
                  {activeFilterCount}
                </UnifiedBadge>
              </div>
              <div className="flex flex-wrap gap-2">
                {filters.search && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Search: "{filters.search}"
                  </UnifiedBadge>
                )}
                {(filters.category && filters.category !== 'all') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Category: {filters.category}
                  </UnifiedBadge>
                )}
                {(filters.psp && filters.psp !== 'all') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    PSP: {filters.psp}
                  </UnifiedBadge>
                )}
                {(filters.company && filters.company !== 'all') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Company: {filters.company}
                  </UnifiedBadge>
                )}
                {(filters.payment_method && filters.payment_method !== 'all') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Method: {filters.payment_method}
                  </UnifiedBadge>
                )}
                {(filters.currency && filters.currency !== 'all') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Currency: {filters.currency}
                  </UnifiedBadge>
                )}
                {(filters.status && filters.status !== 'all') && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Status: {filters.status}
                  </UnifiedBadge>
                )}
                {filters.date_from && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    From: {filters.date_from}
                  </UnifiedBadge>
                )}
                {filters.date_to && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    To: {filters.date_to}
                  </UnifiedBadge>
                )}
                {filters.amount_min && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Min: ₺{filters.amount_min}
                  </UnifiedBadge>
                )}
                {filters.amount_max && (
                  <UnifiedBadge variant="secondary" size="sm" className="bg-white border border-slate-300 text-slate-700">
                    Max: ₺{filters.amount_max}
                  </UnifiedBadge>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="border-t border-slate-200 pt-4 mt-2">
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-600">
                {activeFilterCount > 0 ? (
                  <span>
                    {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} applied · 
                    Showing {Math.min(displayLimit, transactionsLength)} of {transactionsLength} transactions
                  </span>
                ) : (
                  <span>
                    No filters applied · Showing {Math.min(displayLimit, transactionsLength)} transactions
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <UnifiedButton
                  variant="outline"
                  size="sm"
                  onClick={onExportDisplayed}
                  disabled={transactionsLength === 0}
                  icon={<Download className="h-4 w-4" />}
                  iconPosition="left"
                >
                  Export Displayed ({Math.min(displayLimit, transactionsLength)})
                </UnifiedButton>
                <UnifiedButton
                  variant="outline"
                  size="sm"
                  onClick={onExportAll}
                  disabled={exporting}
                  icon={exporting ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-600"></div>
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  iconPosition="left"
                >
                  {exporting ? 'Exporting...' : 'Export All'}
                </UnifiedButton>
                <UnifiedButton
                  variant="outline"
                  size="sm"
                  onClick={onClearAllFilters}
                  disabled={activeFilterCount === 0}
                  icon={<X className="h-4 w-4" />}
                >
                  Clear All
                </UnifiedButton>
                <UnifiedButton
                  variant="primary"
                  size="sm"
                  onClick={onApplyFilters}
                  icon={<RefreshCw className="h-4 w-4" />}
                  iconPosition="left"
                >
                  Apply Filters
                </UnifiedButton>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </UnifiedCard>
  );
}

