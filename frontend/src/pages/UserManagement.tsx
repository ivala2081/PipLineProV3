import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Plus,
  Edit,
  Trash2,
  Shield,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Search,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  X,
  Save,
  Key,
  Mail,
  User,
  UserCheck,
  UserX,
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { api } from '../utils/apiClient';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { SectionHeader } from '../components/ui/SectionHeader';
import EnhancedErrorBoundary from '../components/EnhancedErrorBoundary';
import Modal from '../components/Modal';

interface UserData {
  id: number;
  username: string;
  email: string | null;
  role: string;
  admin_level: number;
  admin_title: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  failed_login_attempts: number;
  account_locked_until: string | null;
  created_by: number | null;
  permissions: Record<string, boolean>;
  active_sessions_count?: number;
  total_sessions_count?: number;
}

interface UserSession {
  id: number;
  user_id: number;
  session_token: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_active: string;
  is_active: boolean;
}

export default function UserManagement() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserData[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showSessionsModal, setShowSessionsModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserData | null>(null);
  const [userSessions, setUserSessions] = useState<UserSession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user',
    admin_level: 0,
    is_active: true,
  });

  // Load users
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/users/');
      if (response.data.success) {
        setUsers(response.data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Filter users by search term
  const filteredUsers = users.filter((user) =>
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (user.email && user.email.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Handle add user
  const handleAddUser = async () => {
    try {
      const response = await api.post('/api/v1/users/', formData);
      if (response.data.success) {
        setShowAddModal(false);
        setFormData({
          username: '',
          email: '',
          password: '',
          role: 'user',
          admin_level: 0,
          is_active: true,
        });
        fetchUsers();
      } else {
        alert(response.data.error || t('user_management.failed_to_create'));
      }
    } catch (error: any) {
      alert(error.response?.data?.error || t('user_management.failed_to_create'));
    }
  };

  // Handle edit user
  const handleEditUser = async () => {
    if (!selectedUser) return;
    try {
      const updateData: any = {
        username: formData.username,
        email: formData.email,
        role: formData.role,
        admin_level: formData.admin_level,
        is_active: formData.is_active,
      };
      
      const response = await api.put(`/api/v1/users/${selectedUser.id}`, updateData);
      if (response.data.success) {
        setShowEditModal(false);
        setSelectedUser(null);
        fetchUsers();
      } else {
        alert(response.data.error || t('user_management.failed_to_update'));
      }
    } catch (error: any) {
      alert(error.response?.data?.error || t('user_management.failed_to_update'));
    }
  };

  // Handle delete user
  const handleDeleteUser = async (user: UserData) => {
    if (!confirm(t('user_management.confirm_delete', { username: user.username }))) {
      return;
    }

    try {
      const response = await api.delete(`/api/v1/users/${user.id}`);
      if (response.data.success) {
        fetchUsers();
      } else {
        alert(response.data.error || t('user_management.failed_to_delete'));
      }
    } catch (error: any) {
      alert(error.response?.data?.error || t('user_management.failed_to_delete'));
    }
  };

  // Handle toggle active
  const handleToggleActive = async (user: UserData) => {
    try {
      const response = await api.post(`/api/v1/users/${user.id}/toggle-active`);
      if (response.data.success) {
        fetchUsers();
      } else {
        alert(response.data.error || t('user_management.failed_to_update_status'));
      }
    } catch (error: any) {
      alert(error.response?.data?.error || t('user_management.failed_to_update_status'));
    }
  };

  // Handle unlock user
  const handleUnlockUser = async (user: UserData) => {
    try {
      const response = await api.post(`/api/v1/users/${user.id}/unlock`);
      if (response.data.success) {
        fetchUsers();
      } else {
        alert(response.data.error || 'Failed to unlock user');
      }
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to unlock user');
    }
  };

  // Handle reset password
  const handleResetPassword = async () => {
    if (!selectedUser) return;
    if (!formData.password || formData.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    try {
      const response = await api.post(`/api/v1/users/${selectedUser.id}/reset-password`, {
        password: formData.password,
      });
      if (response.data.success) {
        setShowPasswordModal(false);
        setFormData({ ...formData, password: '' });
        alert('Password reset successfully');
      } else {
        alert(response.data.error || 'Failed to reset password');
      }
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to reset password');
    }
  };

  // Handle view sessions
  const handleViewSessions = async (user: UserData) => {
    setSelectedUser(user);
    setShowSessionsModal(true);
    setLoadingSessions(true);
    try {
      const response = await api.get(`/api/v1/users/${user.id}/sessions`);
      if (response.data.success) {
        setUserSessions(response.data.sessions);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  // Open edit modal
  const openEditModal = (user: UserData) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email || '',
      password: '',
      role: user.role,
      admin_level: user.admin_level,
      is_active: user.is_active,
    });
    setShowEditModal(true);
  };

  // Open password reset modal
  const openPasswordModal = (user: UserData) => {
    setSelectedUser(user);
    setFormData({ ...formData, password: '' });
    setShowPasswordModal(true);
  };

  // Get role badge color
  const getRoleBadgeColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      case 'user':
        return 'bg-blue-100 text-blue-800';
      case 'viewer':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <EnhancedErrorBoundary>
      <div className="p-6">
        <div className="mb-6">
          <SectionHeader
            title="User Management"
            description="Manage system users, their accounts, and permissions"
            icon={Users}
          />
        </div>

        {/* Actions Bar */}
        <div className="mb-6 flex items-center justify-between gap-4">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search users by username or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={fetchUsers}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button
              onClick={() => {
                setFormData({
                  username: '',
                  email: '',
                  password: '',
                  role: 'user',
                  admin_level: 0,
                  is_active: true,
                });
                setShowAddModal(true);
              }}
              className="flex items-center gap-2 bg-slate-700 hover:bg-slate-800"
            >
              <Plus className="h-4 w-4" />
              Add User
            </Button>
          </div>
        </div>

        {/* Users Table */}
        <Card>
          <CardHeader>
            <CardTitle>Users ({filteredUsers.length})</CardTitle>
            <CardDescription>All system users and their status</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                {searchTerm ? 'No users found matching your search' : 'No users found'}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Username</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Email</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Role</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Last Login</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Sessions</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((user) => (
                      <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-gray-400" />
                            <span className="font-medium text-gray-900">{user.username}</span>
                            {user.admin_level > 0 && (
                              <Badge className="bg-purple-100 text-purple-800 text-xs">
                                {user.admin_title}
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-600">
                          {user.email || <span className="text-gray-400">No email</span>}
                        </td>
                        <td className="py-3 px-4">
                          <Badge className={getRoleBadgeColor(user.role)}>
                            {user.role}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {user.is_active ? (
                              <Badge className="bg-green-100 text-green-800 flex items-center gap-1">
                                <CheckCircle className="h-3 w-3" />
                                Active
                              </Badge>
                            ) : (
                              <Badge className="bg-red-100 text-red-800 flex items-center gap-1">
                                <UserX className="h-3 w-3" />
                                Inactive
                              </Badge>
                            )}
                            {user.account_locked_until && (
                              <Badge className="bg-orange-100 text-orange-800 flex items-center gap-1">
                                <Lock className="h-3 w-3" />
                                Locked
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {formatDate(user.last_login)}
                        </td>
                        <td className="py-3 px-4">
                          <button
                            onClick={() => handleViewSessions(user)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            {user.active_sessions_count || 0} active
                          </button>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewSessions(user)}
                              title={t('user_management.view_sessions')}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditModal(user)}
                              title={t('user_management.edit_user')}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openPasswordModal(user)}
                              title="Reset Password"
                            >
                              <Key className="h-4 w-4" />
                            </Button>
                            {user.account_locked_until && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleUnlockUser(user)}
                                title="Unlock Account"
                                className="text-orange-600 hover:text-orange-800"
                              >
                                <Unlock className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleToggleActive(user)}
                              title={user.is_active ? 'Deactivate' : 'Activate'}
                              className={user.is_active ? 'text-orange-600' : 'text-green-600'}
                            >
                              {user.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteUser(user)}
                              title={t('user_management.delete_user')}
                              className="text-red-600 hover:text-red-800"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Add User Modal */}
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add New User"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username <span className="text-red-500">*</span>
              </label>
              <Input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="Enter username"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="Enter email (optional)"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password <span className="text-red-500">*</span>
              </label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Enter password (min 6 characters)"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-slate-500"
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Admin Level
              </label>
              <select
                value={formData.admin_level}
                onChange={(e) => setFormData({ ...formData, admin_level: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-slate-500"
              >
                <option value="0">Regular User (0)</option>
                <option value="1">Main Admin (1)</option>
                <option value="2">Secondary Admin (2)</option>
                <option value="3">Sub Admin (3)</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active_add"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300"
              />
              <label htmlFor="is_active_add" className="text-sm text-gray-700">
                Active Account
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowAddModal(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleAddUser} className="bg-slate-700 hover:bg-slate-800">
                <Save className="h-4 w-4 mr-2" />
                {t('user_management.create_user')}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Edit User Modal */}
        <Modal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title={`${t('user_management.edit_user')}: ${selectedUser?.username}`}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username <span className="text-red-500">*</span>
              </label>
              <Input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-slate-500"
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Admin Level
              </label>
              <select
                value={formData.admin_level}
                onChange={(e) => setFormData({ ...formData, admin_level: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-slate-500"
                disabled={selectedUser?.admin_level === 0}
              >
                <option value="0">Regular User (0)</option>
                <option value="1">Main Admin (1)</option>
                <option value="2">Secondary Admin (2)</option>
                <option value="3">Sub Admin (3)</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active_edit"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded border-gray-300"
                disabled={selectedUser?.admin_level === 0}
              />
              <label htmlFor="is_active_edit" className="text-sm text-gray-700">
                Active Account
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowEditModal(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleEditUser} className="bg-slate-700 hover:bg-slate-800">
                <Save className="h-4 w-4 mr-2" />
                {t('user_management.save_changes')}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Password Reset Modal */}
        <Modal
          isOpen={showPasswordModal}
          onClose={() => setShowPasswordModal(false)}
          title={t('user_management.reset_password_for', { username: selectedUser?.username || '' })}
        >
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <p className="text-sm text-blue-800">
                {t('user_management.enter_new_password')}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('user_management.new_password')} <span className="text-red-500">*</span>
              </label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder={t('user_management.enter_new_password_placeholder')}
                required
              />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowPasswordModal(false)}>
                {t('common.cancel')}
              </Button>
              <Button onClick={handleResetPassword} className="bg-slate-700 hover:bg-slate-800">
                <Key className="h-4 w-4 mr-2" />
                {t('user_management.reset_password')}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Sessions Modal */}
        <Modal
          isOpen={showSessionsModal}
          onClose={() => setShowSessionsModal(false)}
          title={t('user_management.sessions_for', { username: selectedUser?.username || '' })}
          size="large"
        >
          <div className="space-y-4">
            {loadingSessions ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : userSessions.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                {t('user_management.no_sessions_found')}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-4 font-medium text-gray-700">{t('user_management.status')}</th>
                      <th className="text-left py-2 px-4 font-medium text-gray-700">{t('user_management.ip_address')}</th>
                      <th className="text-left py-2 px-4 font-medium text-gray-700">{t('user_management.user_agent')}</th>
                      <th className="text-left py-2 px-4 font-medium text-gray-700">{t('user_management.created')}</th>
                      <th className="text-left py-2 px-4 font-medium text-gray-700">{t('user_management.last_active')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userSessions.map((session) => (
                      <tr key={session.id} className="border-b border-gray-100">
                        <td className="py-2 px-4">
                          {session.is_active ? (
                            <Badge className="bg-green-100 text-green-800">{t('user_management.active')}</Badge>
                          ) : (
                            <Badge className="bg-gray-100 text-gray-800">{t('user_management.inactive')}</Badge>
                          )}
                        </td>
                        <td className="py-2 px-4 text-sm text-gray-600">{session.ip_address || 'N/A'}</td>
                        <td className="py-2 px-4 text-sm text-gray-600">
                          {session.user_agent ? (
                            <span className="max-w-xs truncate block" title={session.user_agent}>
                              {session.user_agent}
                            </span>
                          ) : (
                            'N/A'
                          )}
                        </td>
                        <td className="py-2 px-4 text-sm text-gray-600">{formatDate(session.created_at)}</td>
                        <td className="py-2 px-4 text-sm text-gray-600">{formatDate(session.last_active)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="flex justify-end pt-4">
              <Button variant="outline" onClick={() => setShowSessionsModal(false)}>
                {t('common.close')}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </EnhancedErrorBoundary>
  );
}

