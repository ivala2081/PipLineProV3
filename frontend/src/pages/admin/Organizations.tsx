/**
 * Organizations Management Page
 * Allows super admins to view, create, edit, and delete organizations
 */
import React, { useState, useEffect } from 'react';
import { UnifiedCard, UnifiedButton, UnifiedBadge, UnifiedInput } from '../../design-system';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { apiClient } from '../../utils/apiClient';
import { Plus, Edit2, Trash2, Users, Building2, Search, X, Save, Loader2 } from 'lucide-react';

interface Organization {
  id: number;
  name: string;
  slug: string;
  subscription_tier: string;
  subscription_status: string;
  max_users: number;
  max_transactions_per_month: number;
  max_psp_connections: number;
  is_active: boolean;
  contact_email?: string;
  created_at: string;
}

export default function Organizations() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    subscription_tier: 'free',
    max_users: 1,
    max_transactions_per_month: 100,
    max_psp_connections: 1,
    contact_email: '',
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      console.log('Fetching organizations...');
      const response = await apiClient.get('/organizations');
      console.log('Organizations API response:', response);
      console.log('Organizations data:', response.data);
      
      // apiClient returns { data, status, headers, ok }
      // Backend returns { success: True, organizations: [...], count: ... }
      const orgs = response.data?.organizations || [];
      console.log(`Found ${orgs.length} organizations:`, orgs);
      setOrganizations(orgs);
    } catch (error: any) {
      console.error('Failed to fetch organizations:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        response: error.response,
        data: error.data
      });
      alert(`Failed to fetch organizations: ${error.data?.error || error.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      console.log('Creating/updating organization with data:', formData);
      
      let response;
      if (editingOrg) {
        response = await apiClient.put(`/organizations/${editingOrg.id}`, formData);
      } else {
        response = await apiClient.post('/organizations', formData);
      }
      
      console.log('API Response:', response);
      console.log('Response data:', response.data);
      
      if (response.data?.success) {
        console.log('Organization saved successfully:', response.data.organization);
        alert(`Organization ${editingOrg ? 'updated' : 'created'} successfully!`);
      } else {
        console.warn('Unexpected response format:', response);
      }
      
      setShowForm(false);
      setEditingOrg(null);
      setFormData({
        name: '',
        slug: '',
        subscription_tier: 'free',
        max_users: 1,
        max_transactions_per_month: 100,
        max_psp_connections: 1,
        contact_email: '',
      });
      
      // Refresh immediately - the API should have committed
      await fetchOrganizations();
    } catch (error: any) {
      console.error('Failed to save organization:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        response: error.response,
        data: error.data
      });
      
      const errorMessage = error.data?.error || error.response?.data?.error || error.message || 'Failed to save organization';
      const status = error.status || error.response?.status || 'Unknown';
      
      alert(`Error: ${errorMessage}\n\nStatus: ${status}\n\nPlease check:\n1. You are logged in as a Super Admin (admin_level 0 or 1)\n2. The organization name and slug are valid\n3. The slug is unique\n4. Check browser console for more details`);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (org: Organization) => {
    setEditingOrg(org);
    setFormData({
      name: org.name,
      slug: org.slug,
      subscription_tier: org.subscription_tier,
      max_users: org.max_users,
      max_transactions_per_month: org.max_transactions_per_month,
      max_psp_connections: org.max_psp_connections,
      contact_email: org.contact_email || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (orgId: number) => {
    if (!confirm('Are you sure you want to delete this organization? This action cannot be undone.')) {
      return;
    }
    
    try {
      await apiClient.delete(`/organizations/${orgId}`);
      fetchOrganizations();
    } catch (error: any) {
      console.error('Failed to delete organization:', error);
      alert(error.response?.data?.error || 'Failed to delete organization');
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingOrg(null);
    setFormData({
      name: '',
      slug: '',
      subscription_tier: 'free',
      max_users: 1,
      max_transactions_per_month: 100,
      max_psp_connections: 1,
      contact_email: '',
    });
  };

  const filteredOrgs = organizations.filter(org =>
    org.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    org.slug.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getTierBadge = (tier: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'outline'> = {
      free: 'secondary',
      starter: 'outline',
      pro: 'default',
      enterprise: 'default',
    };
    return (
      <UnifiedBadge variant={variants[tier] || 'secondary'} size="sm">
        {tier.toUpperCase()}
      </UnifiedBadge>
    );
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'destructive'> = {
      active: 'success',
      suspended: 'warning',
      cancelled: 'destructive',
    };
    return (
      <UnifiedBadge variant={variants[status] || 'secondary'} size="sm">
        {status}
      </UnifiedBadge>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <SectionHeader
        title="Organizations"
        description="Manage organizations and their subscriptions"
        icon={Building2}
        actions={
          !showForm && (
            <UnifiedButton
              onClick={() => {
                setEditingOrg(null);
                setFormData({
                  name: '',
                  slug: '',
                  subscription_tier: 'free',
                  max_users: 1,
                  max_transactions_per_month: 100,
                  max_psp_connections: 1,
                  contact_email: '',
                });
                setShowForm(true);
              }}
              icon={<Plus className="w-4 h-4" />}
            >
              Create Organization
            </UnifiedButton>
          )
        }
        showDivider
      />

      {/* Search Bar */}
      {!showForm && (
        <div className="max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search organizations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      )}

      {/* Form Card */}
      {showForm && (
        <UnifiedCard variant="outlined" className="border-gray-200">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              {editingOrg ? 'Edit Organization' : 'Create New Organization'}
            </h2>
            <button
              onClick={handleCancel}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <form onSubmit={handleCreateOrUpdate} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Name *
                </label>
                <Input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Company ABC"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Slug (URL-friendly) *
                </label>
                <Input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') })}
                  placeholder="company-abc"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">Lowercase letters, numbers, and hyphens only</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subscription Tier
                </label>
                <Select
                  value={formData.subscription_tier}
                  onChange={(e) => setFormData({ ...formData, subscription_tier: e.target.value })}
                >
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Contact Email
                </label>
                <Input
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  placeholder="contact@company.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Users
                </label>
                <Input
                  type="number"
                  value={formData.max_users}
                  onChange={(e) => setFormData({ ...formData, max_users: parseInt(e.target.value) || 1 })}
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Transactions/Month
                </label>
                <Input
                  type="number"
                  value={formData.max_transactions_per_month}
                  onChange={(e) => setFormData({ ...formData, max_transactions_per_month: parseInt(e.target.value) || 100 })}
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max PSP Connections
                </label>
                <Input
                  type="number"
                  value={formData.max_psp_connections}
                  onChange={(e) => setFormData({ ...formData, max_psp_connections: parseInt(e.target.value) || 1 })}
                  min="1"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
              <UnifiedButton
                type="button"
                variant="secondary"
                onClick={handleCancel}
                disabled={saving}
              >
                Cancel
              </UnifiedButton>
              <UnifiedButton
                type="submit"
                disabled={saving}
                loading={saving}
                icon={saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              >
                {editingOrg ? 'Update Organization' : 'Create Organization'}
              </UnifiedButton>
            </div>
          </form>
        </UnifiedCard>
      )}

      {/* Organizations Grid */}
      {!showForm && (
        <>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading organizations...</span>
            </div>
          ) : filteredOrgs.length === 0 ? (
            <UnifiedCard variant="outlined" className="text-center py-12">
              <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">
                {searchTerm ? 'No organizations found matching your search.' : 'No organizations yet.'}
              </p>
              {!searchTerm && (
                <UnifiedButton
                  variant="outline"
                  onClick={() => setShowForm(true)}
                  className="mt-4"
                >
                  Create Your First Organization
                </UnifiedButton>
              )}
            </UnifiedCard>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredOrgs.map((org) => (
                <UnifiedCard
                  key={org.id}
                  variant="outlined"
                  className="hover:shadow-md transition-all duration-200 border-gray-200"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-gray-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{org.name}</h3>
                        <code className="text-xs text-gray-500 bg-gray-50 px-2 py-0.5 rounded mt-1 block">
                          {org.slug}
                        </code>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleEdit(org)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="Edit"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      {org.id !== 1 && (
                        <button
                          onClick={() => handleDelete(org.id)}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">Tier:</span>
                      {getTierBadge(org.subscription_tier)}
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">Status:</span>
                      {getStatusBadge(org.subscription_status)}
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span>Max {org.max_users} users</span>
                    </div>

                    {org.contact_email && (
                      <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
                        {org.contact_email}
                      </div>
                    )}

                    <div className="text-xs text-gray-400 pt-2 border-t border-gray-100">
                      Created {new Date(org.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </UnifiedCard>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
