import { useState, useEffect } from 'react';
import {
  Shield,
  Users,
  Activity,
  AlertTriangle,
  Lock,
  Eye,
  EyeOff,
  LogOut,
  Clock,
  Globe,
  CheckCircle,
  XCircle,
  RefreshCw,
  Download,
  Filter,
} from 'lucide-react';
import { UnifiedCard, UnifiedButton, UnifiedBadge } from '../design-system';
import { api } from '../utils/apiClient';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

interface SecurityOverview {
  active_sessions: number;
  recent_failed_logins: number;
  locked_accounts: number;
  recent_audit_entries: number;
  critical_actions_week: number;
}

interface UserSession {
  id: number;
  username: string;
  role: string;
  ip_address: string;
  user_agent: string;
  created_at: string;
  last_active: string;
  is_active: boolean;
}

interface LoginAttempt {
  id: number;
  username: string;
  ip_address: string;
  success: boolean;
  timestamp: string;
  failure_reason?: string;
  user_agent?: string;
}

interface AuditLog {
  id: number;
  username: string;
  action: string;
  table_name: string;
  record_id: number;
  timestamp: string;
  ip_address: string;
  old_values?: string;
  new_values?: string;
}

interface LoginStats {
  total_attempts: number;
  failed_attempts: number;
  success_rate: number;
  failed_ips: number;
  locked_accounts: number;
  top_failed_ips: Array<{ ip: string; count: number }>;
}

export default function SecurityManagement() {
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState<SecurityOverview | null>(null);
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loginAttempts, setLoginAttempts] = useState<LoginAttempt[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loginStats, setLoginStats] = useState<LoginStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    username: '',
    ip_address: '',
    action: '',
    days: 7,
  });

  useEffect(() => {
    fetchSecurityOverview();
  }, []);

  useEffect(() => {
    if (activeTab === 'sessions') {
      fetchSessions();
    } else if (activeTab === 'logins') {
      fetchLoginAttempts();
      fetchLoginStats();
    } else if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, filters]);

  const fetchSecurityOverview = async () => {
    try {
      const response = await api.get('/api/v1/security/security-overview');
      if (response.data.success) {
        setOverview(response.data.overview);
      }
    } catch (error) {
      console.error('Error fetching security overview:', error);
    }
  };

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/security/sessions');
      if (response.data.success) {
        setSessions(response.data.sessions);
      }
    } catch (error) {
      console.error('Error:', 'Failed to fetch sessions');
    } finally {
      setLoading(false);
    }
  };

  const fetchLoginAttempts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.username) params.append('username', filters.username);
      if (filters.ip_address) params.append('ip_address', filters.ip_address);
      params.append('days', filters.days.toString());
      
      const response = await api.get(`/api/v1/security/login-attempts?${params}`);
      if (response.data.success) {
        setLoginAttempts(response.data.attempts);
      }
    } catch (error) {
      console.error('Error:', 'Failed to fetch login attempts');
    } finally {
      setLoading(false);
    }
  };

  const fetchLoginStats = async () => {
    try {
      const response = await api.get(`/api/v1/security/login-attempts/stats?days=${filters.days}`);
      if (response.data.success) {
        setLoginStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error fetching login stats:', error);
    }
  };

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.username) params.append('username', filters.username);
      if (filters.action) params.append('action', filters.action);
      params.append('days', filters.days.toString());
      
      const response = await api.get(`/api/v1/security/audit-logs?${params}`);
      if (response.data.success) {
        setAuditLogs(response.data.logs);
      }
    } catch (error) {
      console.error('Error:', 'Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  const handleTerminateSession = async (sessionId: number) => {
    if (!confirm('Are you sure you want to terminate this session?')) return;

    try {
      const response = await api.delete(`/api/v1/security/sessions/${sessionId}`);
      if (response.data.success) {
        console.log('✅ Success:', 'Session terminated successfully');
        fetchSessions();
        fetchSecurityOverview();
      }
    } catch (error) {
      console.error('Error:', 'Failed to terminate session');
    }
  };

  const handleTerminateAllUserSessions = async (userId: number, username: string) => {
    if (!confirm(`Terminate all sessions for user "${username}"?`)) return;

    try {
      const response = await api.delete(`/api/v1/security/sessions/user/${userId}`);
      if (response.data.success) {
        console.log('✅ Success:', `${response.data.count} sessions terminated`);
        fetchSessions();
        fetchSecurityOverview();
      }
    } catch (error) {
      console.error('Error:', 'Failed to terminate sessions');
    }
  };

  const handleUnlockAccount = async (userId: number) => {
    try {
      const response = await api.post(`/api/v1/security/users/${userId}/unlock`);
      if (response.data.success) {
        console.log('✅ Success:', 'Account unlocked successfully');
        fetchSessions();
      }
    } catch (error) {
      console.error('Error:', 'Failed to unlock account');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatRelativeTime = (dateString: string) => {
    const diff = Date.now() - new Date(dateString).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  return (
    <div className="space-y-6">
      {/* Security Overview */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2 text-xs">
                <Users className="h-4 w-4 text-blue-500" />
                Active Sessions
              </CardDescription>
              <CardTitle className="text-3xl font-bold text-blue-600">
                {overview.active_sessions}
              </CardTitle>
            </CardHeader>
          </Card>

          <Card className="border-l-4 border-l-red-500">
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2 text-xs">
                <XCircle className="h-4 w-4 text-red-500" />
                Failed Logins (24h)
              </CardDescription>
              <CardTitle className="text-3xl font-bold text-red-600">
                {overview.recent_failed_logins}
              </CardTitle>
            </CardHeader>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2 text-xs">
                <Lock className="h-4 w-4 text-orange-500" />
                Locked Accounts
              </CardDescription>
              <CardTitle className="text-3xl font-bold text-orange-600">
                {overview.locked_accounts}
              </CardTitle>
            </CardHeader>
          </Card>

          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2 text-xs">
                <Activity className="h-4 w-4 text-green-500" />
                Audit Entries (24h)
              </CardDescription>
              <CardTitle className="text-3xl font-bold text-green-600">
                {overview.recent_audit_entries}
              </CardTitle>
            </CardHeader>
          </Card>

          <Card className="border-l-4 border-l-purple-500">
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2 text-xs">
                <AlertTriangle className="h-4 w-4 text-purple-500" />
                Critical Actions (7d)
              </CardDescription>
              <CardTitle className="text-3xl font-bold text-purple-600">
                {overview.critical_actions_week}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* Security Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="sessions" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Sessions
          </TabsTrigger>
          <TabsTrigger value="logins" className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            Login Attempts
          </TabsTrigger>
          <TabsTrigger value="audit" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Audit Logs
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-indigo-600" />
                Security Dashboard
              </CardTitle>
              <CardDescription>
                Monitor system security status and recent activity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold text-sm text-gray-700 mb-3">Quick Actions</h4>
                  <div className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('sessions')}
                    >
                      <Users className="h-4 w-4 mr-2" />
                      Manage Sessions
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('logins')}
                    >
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Review Failed Logins
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('audit')}
                    >
                      <Activity className="h-4 w-4 mr-2" />
                      View Audit Trail
                    </Button>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold text-sm text-gray-700 mb-3">Security Status</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Session Security</span>
                      <Badge variant="default" className="bg-green-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">CSRF Protection</span>
                      <Badge variant="default" className="bg-green-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Enabled
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Rate Limiting</span>
                      <Badge variant="default" className="bg-green-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sessions Tab */}
        <TabsContent value="sessions" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Active Sessions</CardTitle>
                  <CardDescription>Manage active user sessions and force logout</CardDescription>
                </div>
                <Button onClick={fetchSessions} variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-gray-500">Loading sessions...</div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No active sessions found</p>
                  <p className="text-sm text-gray-400 mt-1">All users have been logged out</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Users className="h-5 w-5 text-indigo-600" />
                            <div>
                              <h4 className="font-semibold text-gray-900">{session.username}</h4>
                              <Badge variant="secondary" className="text-xs">
                                {session.role}
                              </Badge>
                            </div>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm text-gray-600 mt-3">
                            <div className="flex items-center gap-2">
                              <Globe className="h-4 w-4" />
                              <span className="font-mono">{session.ip_address}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4" />
                              <span>{formatRelativeTime(session.last_active)}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {session.is_active ? (
                                <Badge variant="default" className="bg-green-500">Active</Badge>
                              ) : (
                                <Badge variant="secondary">Inactive</Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        {session.is_active && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleTerminateSession(session.id)}
                          >
                            <LogOut className="h-4 w-4 mr-2" />
                            Logout
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Login Attempts Tab */}
        <TabsContent value="logins" className="space-y-4">
          {loginStats && (
            <Card>
              <CardHeader>
                <CardTitle>Login Statistics</CardTitle>
                <CardDescription>Last {filters.days} days</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{loginStats.total_attempts}</div>
                    <div className="text-xs text-gray-600">Total Attempts</div>
                  </div>
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{loginStats.failed_attempts}</div>
                    <div className="text-xs text-gray-600">Failed</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{loginStats.success_rate}%</div>
                    <div className="text-xs text-gray-600">Success Rate</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">{loginStats.locked_accounts}</div>
                    <div className="text-xs text-gray-600">Locked Accounts</div>
                  </div>
                </div>

                {loginStats.top_failed_ips.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-semibold text-sm text-gray-700 mb-2">Top Failed IPs</h4>
                    <div className="space-y-1">
                      {loginStats.top_failed_ips.map((item, index) => (
                        <div key={index} className="flex items-center justify-between text-sm">
                          <span className="font-mono text-gray-600">{item.ip}</span>
                          <Badge variant="destructive">{item.count} failed</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Login Attempts</CardTitle>
                  <CardDescription>Monitor successful and failed login attempts</CardDescription>
                </div>
                <div className="flex gap-2">
                  <select
                    className="px-3 py-1 border rounded-md text-sm"
                    value={filters.days}
                    onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
                  >
                    <option value={1}>Last 24 hours</option>
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                  </select>
                  <Button onClick={fetchLoginAttempts} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-gray-500">Loading login attempts...</div>
              ) : loginAttempts.length === 0 ? (
                <div className="text-center py-8">
                  <Lock className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No login attempts found</p>
                  <p className="text-sm text-gray-400 mt-1">Try adjusting the date range</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {loginAttempts.map((attempt) => (
                    <div
                      key={attempt.id}
                      className={`p-3 rounded-lg border ${
                        attempt.success
                          ? 'bg-green-50 border-green-200'
                          : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {attempt.success ? (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-600" />
                          )}
                          <div>
                            <div className="font-semibold text-gray-900">{attempt.username}</div>
                            <div className="text-sm text-gray-600">
                              <span className="font-mono">{attempt.ip_address}</span>
                              {attempt.failure_reason && (
                                <span className="ml-2 text-red-600">• {attempt.failure_reason}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-500">
                            {formatDate(attempt.timestamp)}
                          </div>
                          <Badge
                            variant={attempt.success ? 'default' : 'destructive'}
                            className={attempt.success ? 'bg-green-500' : ''}
                          >
                            {attempt.success ? 'Success' : 'Failed'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Logs Tab */}
        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Audit Trail</CardTitle>
                  <CardDescription>Complete history of system activities</CardDescription>
                </div>
                <div className="flex gap-2">
                  <select
                    className="px-3 py-1 border rounded-md text-sm"
                    value={filters.days}
                    onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
                  >
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={90}>Last 90 days</option>
                  </select>
                  <Button onClick={fetchAuditLogs} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-gray-500">Loading audit logs...</div>
              ) : auditLogs.length === 0 ? (
                <div className="text-center py-8">
                  <Activity className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No audit logs found</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Audit logs are created when users perform actions like creating, editing, or deleting data
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {auditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="p-3 border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <Activity className="h-5 w-5 text-indigo-600 mt-0.5" />
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-semibold text-gray-900">{log.username}</span>
                              <Badge
                                variant={
                                  log.action === 'DELETE'
                                    ? 'destructive'
                                    : log.action === 'CREATE'
                                    ? 'default'
                                    : 'secondary'
                                }
                                className={
                                  log.action === 'CREATE' ? 'bg-green-500' : ''
                                }
                              >
                                {log.action}
                              </Badge>
                              <span className="text-sm text-gray-600">
                                {log.table_name} #{log.record_id}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 space-y-1">
                              <div className="flex items-center gap-2">
                                <Globe className="h-3 w-3" />
                                <span className="font-mono">{log.ip_address}</span>
                              </div>
                              {log.new_values && (
                                <div className="text-xs bg-gray-50 p-2 rounded font-mono">
                                  {log.new_values.substring(0, 100)}
                                  {log.new_values.length > 100 && '...'}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right text-sm text-gray-500">
                          {formatDate(log.timestamp)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

