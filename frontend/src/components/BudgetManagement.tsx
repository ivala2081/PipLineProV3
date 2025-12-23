import React, { useEffect, useState } from 'react';
import {
  Plus,
  Edit,
  Trash2,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  DollarSign,
  RefreshCw,
  Save,
  X
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { api } from '../utils/apiClient';
import { useNotifications } from '../hooks/useNotifications';

interface BudgetManagementProps {
  currency?: 'USD' | 'TRY' | 'USDT';
}

export default function BudgetManagement({ currency = 'USD' }: BudgetManagementProps) {
  const [budgets, setBudgets] = useState<any[]>([]);
  const [budgetStatus, setBudgetStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingBudget, setEditingBudget] = useState<any>(null);
  const { success: showSuccess, error: showError } = useNotifications();

  // Form state
  const [formData, setFormData] = useState({
    budget_period: new Date().toISOString().slice(0, 7), // YYYY-MM
    category: 'overall',
    budget_usd: '',
    budget_try: '',
    budget_usdt: '',
    warning_threshold: '80',
    alert_threshold: '100',
    notes: ''
  });

  const fetchBudgets = async () => {
    try {
      setLoading(true);
      const response = await api.get('/accounting/budgets?is_active=true');
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setBudgets(data.budgets);
        }
      }
    } catch (err) {
      console.error('Error loading budgets:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBudgetStatus = async () => {
    try {
      const currentPeriod = new Date().toISOString().slice(0, 7);
      const response = await api.get(`/accounting/budgets/status?budget_period=${currentPeriod}&currency=${currency}`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          setBudgetStatus(data.data);
        }
      }
    } catch (err) {
      console.error('Error loading budget status:', err);
    }
  };

  useEffect(() => {
    fetchBudgets();
    fetchBudgetStatus();
  }, [currency]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const payload = {
        ...formData,
        budget_usd: parseFloat(formData.budget_usd) || 0,
        budget_try: parseFloat(formData.budget_try) || 0,
        budget_usdt: parseFloat(formData.budget_usdt) || 0,
        warning_threshold: parseInt(formData.warning_threshold) || 80,
        alert_threshold: parseInt(formData.alert_threshold) || 100,
        category: formData.category === 'overall' ? null : formData.category
      };

      let response;
      if (editingBudget) {
        response = await api.put(`/accounting/budgets/${editingBudget.id}`, payload);
      } else {
        response = await api.post('/accounting/budgets', payload);
      }

      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          showSuccess(editingBudget ? 'Budget updated successfully' : 'Budget created successfully');
          setShowAddForm(false);
          setEditingBudget(null);
          resetForm();
          fetchBudgets();
          fetchBudgetStatus();
        } else {
          showError(data.error || 'Failed to save budget');
        }
      }
    } catch (err) {
      console.error('Error saving budget:', err);
      showError('Failed to save budget');
    }
  };

  const handleDelete = async (budgetId: number) => {
    if (!confirm('Are you sure you want to delete this budget?')) return;

    try {
      const response = await api.delete(`/accounting/budgets/${budgetId}`);
      if (response.ok) {
        const data = await api.parseResponse(response);
        if (data.success) {
          showSuccess('Budget deleted successfully');
          fetchBudgets();
          fetchBudgetStatus();
        } else {
          showError(data.error || 'Failed to delete budget');
        }
      }
    } catch (err) {
      console.error('Error deleting budget:', err);
      showError('Failed to delete budget');
    }
  };

  const handleEdit = (budget: any) => {
    setEditingBudget(budget);
    setFormData({
      budget_period: budget.budget_period,
      category: budget.category || 'overall',
      budget_usd: budget.budget_usd.toString(),
      budget_try: budget.budget_try.toString(),
      budget_usdt: budget.budget_usdt.toString(),
      warning_threshold: budget.warning_threshold.toString(),
      alert_threshold: budget.alert_threshold.toString(),
      notes: budget.notes || ''
    });
    setShowAddForm(true);
  };

  const resetForm = () => {
    setFormData({
      budget_period: new Date().toISOString().slice(0, 7),
      category: 'overall',
      budget_usd: '',
      budget_try: '',
      budget_usdt: '',
      warning_threshold: '80',
      alert_threshold: '100',
      notes: ''
    });
  };

  const currencySymbol = currency === 'USD' ? '$' : currency === 'TRY' ? '₺' : 'USDT';

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'bg-green-100 border-green-300 text-green-900';
      case 'warning': return 'bg-orange-100 border-orange-300 text-orange-900';
      case 'alert': return 'bg-red-100 border-red-300 text-red-900';
      default: return 'bg-gray-100 border-gray-300 text-gray-900';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      case 'alert': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Budget Management</h2>
          <p className="text-sm text-gray-600 mt-1">Set and track expense budgets</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchBudgetStatus} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          {!showAddForm && (
            <Button 
              onClick={() => {
                setShowAddForm(true);
                setEditingBudget(null);
                resetForm();
              }}
              className="bg-gray-900 hover:bg-gray-800 text-white"
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Budget
            </Button>
          )}
        </div>
      </div>

      {/* Add/Edit Budget Form */}
      {showAddForm && (
        <Card className="border-gray-300">
          <CardHeader className="bg-gray-50">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold text-gray-900">
                {editingBudget ? 'Edit Budget' : 'Add New Budget'}
              </CardTitle>
              <Button
                onClick={() => {
                  setShowAddForm(false);
                  setEditingBudget(null);
                  resetForm();
                }}
                variant="outline"
                size="sm"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Budget Period *</label>
                  <Input
                    type="month"
                    value={formData.budget_period}
                    onChange={(e) => setFormData({ ...formData, budget_period: e.target.value })}
                    required
                    className="border-gray-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 bg-white text-sm"
                  >
                    <option value="overall">Overall (All)</option>
                    <option value="inflow">Inflow Only</option>
                    <option value="outflow">Outflow Only</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Budget (USD)</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={formData.budget_usd}
                    onChange={(e) => setFormData({ ...formData, budget_usd: e.target.value })}
                    className="border-gray-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Budget (TRY)</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={formData.budget_try}
                    onChange={(e) => setFormData({ ...formData, budget_try: e.target.value })}
                    className="border-gray-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Budget (USDT)</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={formData.budget_usdt}
                    onChange={(e) => setFormData({ ...formData, budget_usdt: e.target.value })}
                    className="border-gray-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Warning Threshold (%)</label>
                  <Input
                    type="number"
                    min="0"
                    max="200"
                    placeholder="80"
                    value={formData.warning_threshold}
                    onChange={(e) => setFormData({ ...formData, warning_threshold: e.target.value })}
                    className="border-gray-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">Alert Threshold (%)</label>
                  <Input
                    type="number"
                    min="0"
                    max="200"
                    placeholder="100"
                    value={formData.alert_threshold}
                    onChange={(e) => setFormData({ ...formData, alert_threshold: e.target.value })}
                    className="border-gray-200"
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">Notes</label>
                  <Input
                    type="text"
                    placeholder="Optional notes about this budget..."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="border-gray-200"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
                <Button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setEditingBudget(null);
                    resetForm();
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-gray-900 hover:bg-gray-800 text-white">
                  <Save className="h-4 w-4 mr-2" />
                  {editingBudget ? 'Update Budget' : 'Create Budget'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Budget Status Cards */}
      {budgetStatus && budgetStatus.has_budgets && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Current Period: {budgetStatus.budget_period}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {budgetStatus.budgets.map((budget: any) => (
              <Card key={budget.budget_id} className={`border-2 ${getStatusColor(budget.status)}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 capitalize">{budget.category}</h4>
                      <p className="text-xs text-gray-600 mt-1">{budget.expense_count} expenses</p>
                    </div>
                    {getStatusIcon(budget.status)}
                  </div>

                  <div className="space-y-3">
                    {/* Budget vs Actual */}
                    <div>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-700">Budget:</span>
                        <span className="font-semibold text-gray-900">
                          {currencySymbol}{budget.budget_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-gray-700">Actual:</span>
                        <span className="font-semibold text-gray-900">
                          {currencySymbol}{budget.actual_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-3 rounded-full transition-all duration-300 ${
                            budget.status === 'alert' ? 'bg-red-600' :
                            budget.status === 'warning' ? 'bg-orange-500' :
                            'bg-green-600'
                          }`}
                          style={{ width: `${Math.min(budget.usage_percentage, 100)}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        {budget.usage_percentage.toFixed(1)}% used
                      </p>
                    </div>

                    {/* Remaining */}
                    <div className="pt-3 border-t border-gray-300">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">Remaining:</span>
                        <span className={`text-sm font-bold ${
                          budget.remaining_amount < 0 ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {currencySymbol}{budget.remaining_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* All Budgets List */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900">All Budgets</CardTitle>
          <CardDescription>Manage all budget periods</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading budgets...</div>
          ) : budgets.length === 0 ? (
            <div className="text-center py-8">
              <DollarSign className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No budgets created yet</p>
              <Button
                onClick={() => {
                  setShowAddForm(true);
                  setEditingBudget(null);
                  resetForm();
                }}
                variant="outline"
                className="mt-4"
                size="sm"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create First Budget
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {budgets.map((budget) => (
                <div
                  key={budget.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h4 className="font-semibold text-gray-900">{budget.budget_period}</h4>
                      <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded">
                        {budget.category}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      {budget.budget_usd > 0 && <span>${budget.budget_usd.toLocaleString()}</span>}
                      {budget.budget_try > 0 && <span>₺{budget.budget_try.toLocaleString()}</span>}
                      {budget.budget_usdt > 0 && <span>USDT {budget.budget_usdt.toLocaleString()}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={() => handleEdit(budget)}
                      variant="outline"
                      size="sm"
                      className="border-gray-200 hover:border-gray-300"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      onClick={() => handleDelete(budget.id)}
                      variant="outline"
                      size="sm"
                      className="border-red-200 text-red-600 hover:border-red-300 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

