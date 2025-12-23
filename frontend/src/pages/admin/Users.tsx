/**
 * Users Management Page
 * Allows admins to view, create, edit, and manage users
 */
import React, { useState, useEffect } from 'react';
import { UnifiedCard, UnifiedButton, UnifiedBadge, UnifiedTable } from '../../design-system';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { apiClient } from '../../utils/apiClient';
import { Plus, Edit2, Trash2, UserCheck, UserX, Mail, Shield, Search, Building2, X, Save, Loader2 } from 'lucide-react';

interface User {
  id: number;
  username: string;
  email?: string;
  organization_id?: number;
  organization_name?: string;
  admin_level: number;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface Organization {
  id: number;
  name: string;
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterOrg, setFilterOrg] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    organization_id: '',
    admin_level: 3,
    role: 'user',
    is_active: true,
  });

  useEffect(() => {
    fetchUsers();
    fetchOrganizations();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/users');
      setUsers(response.users || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const response = await apiClient.get('/organizations');
      // apiClient returns { data, status, headers, ok }
      // Backend returns { success: True, organizations: [...], count: ... }
      const orgs = response.data?.organizations || [];
      setOrganizations(orgs);
    } catch (error: any) {
      console.error('Failed to fetch organizations:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        data: error.data
      });
    }
  };

  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      const payload = {
        ...formData,
        organization_id: formData.organization_id ? parseInt(formData.organization_id) : null,
      };

      if (editingUser) {
        if (!payload.password) {
          delete (payload as any).password;
        }
        await apiClient.put(`/users/${editingUser.id}`, payload);
      } else {
        if (!payload.password) {
          alert('Password is required for new users');
          return;
        }
        await apiClient.post('/users', payload);
      }
      
      handleCancel();
      fetchUsers();
    } catch (error: any) {
      console.error('Failed to save user:', error);
      alert(error.response?.data?.error || 'Failed to save user');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email || '',
      password: '',
      organization_id: user.organization_id?.toString() || '',
      admin_level: user.admin_level,
      role: user.role,
      is_active: user.is_active,
    });
    setShowForm(true);
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }
    
    try {
      await apiClient.delete(`/users/${userId}`);
      fetchUsers();
    } catch (error: any) {
      console.error('Failed to delete user:', error);
      alert(error.response?.data?.error || 'Failed to delete user');
    }
  };

  const handleActivate = async (userId: number) => {
    try {
      await apiClient.post(`/users/${userId}/activate`);
      fetchUsers();
    } catch (error: any) {
      console.error('Failed to activate user:', error);
      alert(error.response?.data?.error || 'Failed to activate user');
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      organization_id: '',
      admin_level: 3,
      role: 'user',
      is_active: true,
    });
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.organization_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesOrg = filterOrg === 'all' || user.organization_id?.toString() === filterOrg;
    const matchesStatus = filterStatus === 'all' || 
      (filterStatus === 'active' && user.is_active) ||
      (filterStatus === 'inactive' && !user.is_active);
    
    return matchesSearch && matchesOrg && matchesStatus;
  });

  const getAdminLevelBadge = (level: number) => {
    if (level <= 1) {
      return <UnifiedBadge variant="destructive" size="sm">Super Admin</UnifiedBadge>;
    }
    if (level === 2) {
      return <UnifiedBadge variant="info" size="sm">Org Admin</UnifiedBadge>;
    }
    return <UnifiedBadge variant="secondary" size="sm">User</UnifiedBadge>;
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <UnifiedBadge variant="success" size="sm" className="flex items-center gap-1 w-fit">
        <UserCheck className="w-3 h-3" />
        Active
      </UnifiedBadge>
    ) : (
      <UnifiedBadge variant="destructive" size="sm" className="flex items-center gap-1 w-fit">
        <UserX className="w-3 h-3" />
        Inactive
      </UnifiedBadge>
    );
  };

  const tableColumns = [
    {
      key: 'user',
      label: 'User',
      render: (_: any, user: User) => (
        <div>
          <div className="font-medium text-gray-900">{user.username}</div>
          {user.email && (
            <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <Mail className="w-3 h-3" />
              {user.email}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'organization',
      label: 'Organization',
      render: (_: any, user: User) => (
        user.organization_name ? (
          <div className="flex items-center gap-1 text-sm text-gray-900">
            <Building2 className="w-4 h-4 text-gray-400" />
            {user.organization_name}
          </div>
        ) : (
          <span className="text-sm text-gray-400">No org</span>
        )
      ),
    },
    {
      key: 'admin_level',
      label: 'Admin Level',
      render: (_: any, user: User) => getAdminLevelBadge(user.admin_level),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_: any, user: User) => getStatusBadge(user.is_active),
    },
    {
      key: 'created',
      label: 'Created',
      render: (_: any, user: User) => (
        <span className="text-sm text-gray-500">
          {new Date(user.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_: any, user: User) => (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={() => handleEdit(user)}
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
            title="Edit"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          {user.is_active ? (
            <button
              onClick={() => handleDelete(user.id)}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => handleActivate(user.id)}
              className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
              title="Activate"
            >
              <UserCheck className="w-4 h-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <SectionHeader
        title="Users"
        description="Manage user accounts and permissions"
        icon={Shield}
        actions={
          !showForm && (
            <UnifiedButton
              onClick={() => {
                setEditingUser(null);
                setFormData({
                  username: '',
                  email: '',
                  password: '',
                  organization_id: '',
                  admin_level: 3,
                  role: 'user',
                  is_active: true,
                });
                setShowForm(true);
              }}
              icon={<Plus className="w-4 h-4" />}
            >
              Create User
            </UnifiedButton>
          )
        }
        showDivider
      />

      {/* Filters */}
      {!showForm && (
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                type="text"
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <Select
            value={filterOrg}
            onChange={(e) => setFilterOrg(e.target.value)}
            className="w-full md:w-48"
          >
            <option value="all">All Organizations</option>
            {organizations.map(org => (
              <option key={org.id} value={org.id.toString()}>{org.name}</option>
            ))}
          </Select>

          <Select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full md:w-40"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </Select>
        </div>
      )}

      {/* Form Card */}
      {showForm && (
        <UnifiedCard variant="outlined" className="border-gray-200">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              {editingUser ? 'Edit User' : 'Create New User'}
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
                  Username *
                </label>
                <Input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="john.doe"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="john@company.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password {editingUser ? '(leave blank to keep current)' : '*'}
                </label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder={editingUser ? 'Leave blank to keep current' : 'Enter password'}
                  required={!editingUser}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization
                </label>
                <Select
                  value={formData.organization_id}
                  onChange={(e) => setFormData({ ...formData, organization_id: e.target.value })}
                >
                  <option value="">No Organization</option>
                  {organizations.map(org => (
                    <option key={org.id} value={org.id.toString()}>{org.name}</option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Admin Level
                </label>
                <Select
                  value={formData.admin_level.toString()}
                  onChange={(e) => setFormData({ ...formData, admin_level: parseInt(e.target.value) })}
                >
                  <option value="0">Super Admin (Level 0)</option>
                  <option value="1">Main Admin (Level 1)</option>
                  <option value="2">Org Admin (Level 2)</option>
                  <option value="3">Regular User (Level 3)</option>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role
                </label>
                <Select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="admin">Admin</option>
                  <option value="user">User</option>
                  <option value="viewer">Viewer</option>
                </Select>
              </div>

              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Active</span>
                </label>
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
                {editingUser ? 'Update User' : 'Create User'}
              </UnifiedButton>
            </div>
          </form>
        </UnifiedCard>
      )}

      {/* Users Table */}
      {!showForm && (
        <>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading users...</span>
            </div>
          ) : filteredUsers.length === 0 ? (
            <UnifiedCard variant="outlined" className="text-center py-12">
              <Shield className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">
                {searchTerm || filterOrg !== 'all' || filterStatus !== 'all'
                  ? 'No users found matching your filters.'
                  : 'No users yet.'}
              </p>
              {!searchTerm && filterOrg === 'all' && filterStatus === 'all' && (
                <UnifiedButton
                  variant="outline"
                  onClick={() => setShowForm(true)}
                  className="mt-4"
                >
                  Create Your First User
                </UnifiedButton>
              )}
            </UnifiedCard>
          ) : (
            <UnifiedCard variant="outlined" className="border-gray-200 overflow-hidden">
              <UnifiedTable
                data={filteredUsers}
                columns={tableColumns}
                striped
                hover
                size="md"
              />
            </UnifiedCard>
          )}
        </>
      )}
    </div>
  );
}
