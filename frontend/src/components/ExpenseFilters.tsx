import React from 'react';
import { Search, Filter, X, Calendar, ChevronDown, ChevronUp } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { useLanguage } from '../contexts/LanguageContext';

interface ExpenseFiltersProps {
  // Basic filters
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  statusFilter: 'all' | 'paid' | 'pending' | 'cancelled';
  setStatusFilter: (value: 'all' | 'paid' | 'pending' | 'cancelled') => void;
  categoryFilter: 'all' | 'inflow' | 'outflow';
  setCategoryFilter: (value: 'all' | 'inflow' | 'outflow') => void;
  typeFilter: 'all' | 'payment' | 'transfer';
  setTypeFilter: (value: 'all' | 'payment' | 'transfer') => void;
  
  // Advanced filters
  dateFrom: string;
  setDateFrom: (value: string) => void;
  dateTo: string;
  setDateTo: (value: string) => void;
  costPeriod: string;
  setCostPeriod: (value: string) => void;
  
  // UI state
  showAdvanced: boolean;
  setShowAdvanced: (value: boolean) => void;
  
  // Actions
  onClearAll: () => void;
  onExport: () => void;
  filteredCount: number;
}

export default function ExpenseFilters({
  searchTerm,
  setSearchTerm,
  statusFilter,
  setStatusFilter,
  categoryFilter,
  setCategoryFilter,
  typeFilter,
  setTypeFilter,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  costPeriod,
  setCostPeriod,
  showAdvanced,
  setShowAdvanced,
  onClearAll,
  onExport,
  filteredCount
}: ExpenseFiltersProps) {
  const { t } = useLanguage();

  const hasActiveFilters = searchTerm || statusFilter !== 'all' || categoryFilter !== 'all' || 
    typeFilter !== 'all' || dateFrom || dateTo || costPeriod;

  const activeFilterCount = [
    searchTerm,
    statusFilter !== 'all',
    categoryFilter !== 'all',
    typeFilter !== 'all',
    dateFrom,
    dateTo,
    costPeriod
  ].filter(Boolean).length;

  // Quick filter presets
  const applyQuickFilter = (preset: string) => {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    const lastMonthFirst = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const lastMonthLast = new Date(today.getFullYear(), today.getMonth(), 0);

    switch (preset) {
      case 'this_month':
        setDateFrom(firstDayOfMonth.toISOString().split('T')[0]);
        setDateTo(lastDayOfMonth.toISOString().split('T')[0]);
        break;
      case 'last_month':
        setDateFrom(lastMonthFirst.toISOString().split('T')[0]);
        setDateTo(lastMonthLast.toISOString().split('T')[0]);
        break;
      case 'pending':
        setStatusFilter('pending');
        break;
      case 'paid':
        setStatusFilter('paid');
        break;
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Filter className="h-5 w-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Filters {activeFilterCount > 0 && <span className="text-sm text-gray-500">({activeFilterCount} active)</span>}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <Button
                onClick={onClearAll}
                variant="outline"
                size="sm"
                className="border-gray-200 hover:border-gray-300 hover:bg-gray-50"
              >
                <X className="h-4 w-4 mr-1" />
                Clear All
              </Button>
            )}
            <Button
              onClick={() => setShowAdvanced(!showAdvanced)}
              variant="outline"
              size="sm"
              className="border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            >
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {showAdvanced ? 'Less' : 'More'} Filters
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Filter Presets */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-700">Quick Filters:</span>
          <Button
            onClick={() => applyQuickFilter('this_month')}
            variant="outline"
            size="sm"
            className="border-gray-200 hover:border-gray-400 hover:bg-white"
          >
            <Calendar className="h-3 w-3 mr-1" />
            This Month
          </Button>
          <Button
            onClick={() => applyQuickFilter('last_month')}
            variant="outline"
            size="sm"
            className="border-gray-200 hover:border-gray-400 hover:bg-white"
          >
            <Calendar className="h-3 w-3 mr-1" />
            Last Month
          </Button>
          <Button
            onClick={() => applyQuickFilter('pending')}
            variant="outline"
            size="sm"
            className="border-gray-200 hover:border-gray-400 hover:bg-white"
          >
            Pending
          </Button>
          <Button
            onClick={() => applyQuickFilter('paid')}
            variant="outline"
            size="sm"
            className="border-gray-200 hover:border-gray-400 hover:bg-white"
          >
            Paid
          </Button>
        </div>
      </div>

      {/* Basic Filters */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <Search className="h-4 w-4 text-gray-500" />
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search description, detail, source..."
                className="pl-10 w-full border-gray-200 focus:border-gray-500 focus:ring-gray-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Status Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white text-sm"
            >
              <option value="all">All Status</option>
              <option value="paid">Paid</option>
              <option value="pending">Pending</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white text-sm"
            >
              <option value="all">All Categories</option>
              <option value="inflow">Inflow</option>
              <option value="outflow">Outflow</option>
            </select>
          </div>

          {/* Type Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white text-sm"
            >
              <option value="all">All Types</option>
              <option value="payment">Payment</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Date From */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Date From</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="border-gray-200 focus:border-gray-500 focus:ring-gray-500"
                />
              </div>

              {/* Date To */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Date To</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="border-gray-200 focus:border-gray-500 focus:ring-gray-500"
                />
              </div>

              {/* Cost Period */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Cost Period</label>
                <Input
                  type="text"
                  placeholder="e.g., 2025-01"
                  value={costPeriod}
                  onChange={(e) => setCostPeriod(e.target.value)}
                  className="border-gray-200 focus:border-gray-500 focus:ring-gray-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Results Count & Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            Showing <span className="font-semibold text-gray-900">{filteredCount}</span> expenses
          </div>
          <Button
            onClick={onExport}
            variant="outline"
            size="sm"
            className="border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            disabled={filteredCount === 0}
          >
            Export CSV
          </Button>
        </div>
      </div>
    </div>
  );
}

