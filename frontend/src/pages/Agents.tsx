import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTabPersistence } from '../hooks/useTabPersistence';
import { useLanguage } from '../contexts/LanguageContext';
import StandardMetricsCard from '../components/StandardMetricsCard';
import {
  Search,
  Filter,
  Plus,
  Download,
  Eye,
  Edit,
  Trash2,
  DollarSign,
  TrendingUp,
  Mail,
  Phone,
  Users,
  Activity,
  Target,
  Award,
  Building2,
  BarChart3,
  LineChart,
  X,
  MoreHorizontal,
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

interface Agent {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: string;
  department: string;
  status: 'active' | 'inactive';
  hireDate: string;
  totalTransactions: number;
  performance: number;
  companyName?: string;
  nickname?: string;
  salary?: number;
  insurance?: boolean;
}

interface NewAgent {
  startDate: string;
  companyName: string;
  nickname: string;
  salary: number;
  insurance: boolean;
  name: string;
  email: string;
  phone: string;
  role: string;
  department: string;
}

export default function Agents() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [activeDepartmentTab, setActiveDepartmentTab] = useState('all');
  const [showFilters, setShowFilters] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeTab, handleTabChange] = useTabPersistence<'overview' | 'agents' | 'analytics'>('overview');
  
  // Get departments from localStorage
  const getDepartments = (): string[] => {
    try {
      const savedDepartments = localStorage.getItem('systemDepartments');
      if (savedDepartments) {
        return JSON.parse(savedDepartments);
      }
    } catch (error) {
      console.error('Error loading departments:', error);
    }
    // Default departments if none saved
    return ['Conversion', 'Retention', 'Marketing', 'Research', 'Operation', 'Management', 'Facility'];
  };
  
  const [departments, setDepartments] = useState<string[]>(getDepartments());
  
  // Listen for changes to departments in localStorage
  useEffect(() => {
    const handleStorageChange = () => {
      setDepartments(getDepartments());
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);
  
  // Function to get icon for department
  const getDepartmentIcon = (department: string) => {
    switch (department) {
      case 'Conversion': return TrendingUp;
      case 'Retention': return Target;
      case 'Marketing': return BarChart3;
      case 'Research': return Search;
      case 'Operation': return Activity;
      case 'Management': return Users;
      case 'Facility': return Building2;
      default: return Building2;
    }
  };
  const [newAgent, setNewAgent] = useState<NewAgent>({
    startDate: '',
    companyName: '',
    nickname: '',
    salary: 0,
    insurance: false,
    name: '',
    email: '',
    phone: '',
    role: '',
    department: '',
  });

  const filteredAgents = agents.filter(agent => {
    const matchesSearch =
      agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === 'all' || agent.status === statusFilter;
    const matchesDepartment =
      departmentFilter === 'all' || agent.department === departmentFilter;
    const matchesDepartmentTab =
      activeDepartmentTab === 'all' || agent.department === activeDepartmentTab;

    return matchesSearch && matchesStatus && matchesDepartment && matchesDepartmentTab;
  });

  const totalAgents = filteredAgents.length;
  const activeAgents = filteredAgents.filter(a => a.status === 'active').length;
  const totalTransactions = filteredAgents.reduce(
    (sum, agent) => sum + agent.totalTransactions,
    0
  );
  const avgPerformance =
    filteredAgents.length > 0
      ? Math.round(
          filteredAgents.reduce((sum, agent) => sum + agent.performance, 0) /
            filteredAgents.length
        )
      : 0;

  const resetFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setDepartmentFilter('all');
    setActiveDepartmentTab('all');
  };

  const handleAddAgent = () => {
    setShowAddModal(true);
  };

  const handleCloseAddModal = () => {
    setShowAddModal(false);
    setNewAgent({
      startDate: '',
      companyName: '',
      nickname: '',
      salary: 0,
      insurance: false,
      name: '',
      email: '',
      phone: '',
      role: '',
      department: '',
    });
  };

  const handleInputChange = (field: keyof NewAgent, value: string | number | boolean) => {
    setNewAgent(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmitAgent = () => {
    const agent: Agent = {
      id: Date.now(),
      ...newAgent,
      status: 'active',
      hireDate: newAgent.startDate,
      totalTransactions: 0,
      performance: 85,
    };

    setAgents(prev => [...prev, agent]);
    setNewAgent({
      startDate: '',
      companyName: '',
      nickname: '',
      salary: 0,
      insurance: false,
      name: '',
      email: '',
      phone: '',
      role: '',
      department: '',
    });
    setShowAddModal(false);
  };

  const handleExportAgents = () => {
    // Create CSV content
    const headers = ['Name', 'Email', 'Phone', 'Role', 'Department', 'Status', 'Hire Date', 'Total Transactions', 'Performance', 'Company', 'Nickname', 'Salary', 'Insurance'];
    const csvContent = [
      headers.join(','),
      ...agents.map(agent => [
        `"${agent.name}"`,
        `"${agent.email}"`,
        `"${agent.phone}"`,
        `"${agent.role}"`,
        `"${agent.department}"`,
        `"${agent.status}"`,
        `"${agent.hireDate}"`,
        agent.totalTransactions,
        agent.performance,
        `"${agent.companyName || ''}"`,
        `"${agent.nickname || ''}"`,
        agent.salary || 0,
        agent.insurance ? 'Yes' : 'No'
      ].join(','))
    ].join('\n');

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `agents_export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6">

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Users className="h-8 w-8 text-gray-600" />
              Agent Management
            </h1>
            <p className="text-gray-600">Team management</p>
          </div>
          <div className="flex items-center gap-3">
            <UnifiedButton
              variant="outline"
              size="sm"
              onClick={handleExportAgents}
              icon={<Download className="h-4 w-4" />}
              iconPosition="left"
            >
              Export
            </UnifiedButton>
            <UnifiedButton
              variant="primary"
              size="sm"
              onClick={handleAddAgent}
              icon={<Plus className="h-4 w-4" />}
              iconPosition="left"
            >
              Add Agent
            </UnifiedButton>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">

      {/* Status Indicators */}
      <div className="bg-gray-50/50 border border-gray-200/60 rounded-xl p-4">
        <div className='flex items-center gap-6 text-sm text-gray-700'>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 bg-green-500 rounded-full'></div>
            <span className="font-medium">Active Agents: {activeAgents}</span>
          </div>
          <div className='flex items-center gap-2'>
            <div className='w-2 h-2 bg-gray-500 rounded-full'></div>
                            <span className="font-medium">{t('dashboard.total_transactions')}: {totalTransactions.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className='bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden'>
        <div className='bg-gradient-to-r from-gray-50 to-gray-100/50 px-6 py-2'>
          <nav className='flex space-x-1'>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleTabChange('overview')}
                className={`tab-button px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 flex items-center gap-2 ${
                  activeTab === 'overview'
                    ? 'bg-white text-gray-600 shadow-md border border-gray-200'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <BarChart3 className='h-4 w-4' />
                Overview
              </button>
              {activeTab === 'overview' && (
                <button
                  onClick={() => {
                    // Refresh overview data
                    // Refresh data - could use state management instead
                    window.location.reload(); // Keep for now as it's in error handling
                  }}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white/60 rounded-lg transition-all duration-200 hover:shadow-sm"
                  title="Refresh Overview data"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleTabChange('agents')}
                className={`tab-button px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 flex items-center gap-2 ${
                  activeTab === 'agents'
                    ? 'bg-white text-gray-600 shadow-md border border-gray-200'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <Users className='h-4 w-4' />
                Agents
              </button>
              {activeTab === 'agents' && (
                <button
                  onClick={() => {
                    // Refresh agents data
                    // Refresh data - could use state management instead
                    window.location.reload(); // Keep for now as it's in error handling
                  }}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white/60 rounded-lg transition-all duration-200 hover:shadow-sm"
                  title="Refresh Agents data"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleTabChange('analytics')}
                className={`tab-button px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 flex items-center gap-2 ${
                  activeTab === 'analytics'
                    ? 'bg-white text-gray-600 shadow-md border border-gray-200'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                }`}
              >
                <LineChart className='h-4 w-4' />
                Analytics
              </button>
              {activeTab === 'analytics' && (
                <button
                  onClick={() => {
                    // Refresh analytics data
                    // Refresh data - could use state management instead
                    window.location.reload(); // Keep for now as it's in error handling
                  }}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white/60 rounded-lg transition-all duration-200 hover:shadow-sm"
                  title="Refresh Analytics data"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              )}
            </div>
          </nav>
        </div>
            </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div>
          {/* Enhanced Stats Cards Section */}
          <UnifiedCard variant="elevated" className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-gray-600" />
                Performance Overview
              </CardTitle>
              <CardDescription>
                Key metrics and performance indicators for your agent team
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StandardMetricsCard
                title="Total Agents"
                value={totalAgents}
                subtitle="+5.2% from last month"
                icon={Users}
                color="primary"
                variant="default"
              />

              <StandardMetricsCard
                title="Active Agents"
                value={activeAgents}
                subtitle="+8.7% from last month"
                icon={Activity}
                color="success"
                variant="default"
              />

              <StandardMetricsCard
                title={t('dashboard.total_transactions')}
                value={totalTransactions.toLocaleString()}
                subtitle="+12.3% from last month"
                icon={DollarSign}
                color="orange"
                variant="default"
              />

              <StandardMetricsCard
                title="Avg. Performance"
                value={`${avgPerformance}%`}
                subtitle="+3.1% from last month"
                icon={Award}
                color="purple"
                variant="default"
              />
              </div>
            </CardContent>
          </UnifiedCard>
        </div>
      )}

      {activeTab === 'agents' && (
        <div>
          {/* Enhanced Filters and Search Section */}
          <UnifiedCard variant="elevated" className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-gray-600" />
                Agent Management
              </CardTitle>
              <CardDescription>
                Search, filter, and manage your agent team
              </CardDescription>
            </CardHeader>
            <CardContent>
            {/* Enhanced Filters and Search */}
            <div className='bg-white rounded-xl shadow-sm border border-gray-100'>
              <div className='p-4 border-b border-gray-100'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-2'>
                    <Filter className='h-5 w-5 text-gray-500' />
                    <h3 className='text-lg font-semibold text-gray-900'>
                      Filters
                    </h3>
                    <span className='text-sm text-gray-500'>
                      (
                      {[searchTerm, statusFilter, departmentFilter].filter(
                        v => v && v !== 'all'
                      ).length}{' '}
                      active)
                    </span>
                  </div>
                  <div className='flex items-center gap-2'>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={resetFilters}
                      className="flex items-center gap-2"
                      aria-label="Reset filters"
                    >
                      Reset
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowFilters(!showFilters)}
                      className="flex items-center gap-2"
                      aria-label={showFilters ? 'Hide filters' : 'Show filters'}
                    >
                      <Filter
                        className={`h-4 w-4 transition-transform duration-200 ${showFilters ? 'rotate-180' : ''}`}
                        aria-hidden="true"
                      />
                      {showFilters ? 'Hide' : 'Show'} Filters
                    </Button>
                  </div>
                </div>
              </div>

              {showFilters && (
                <div className='p-6 space-y-6'>
                  {/* Search Row */}
                  <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-2'>
                        Search Agents
                      </label>
                      <div className='relative'>
                        <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
                        <input
                          type='text'
                          placeholder='Search by name or email...'
                          value={searchTerm}
                          onChange={e => setSearchTerm(e.target.value)}
                          className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                        />
                      </div>
                    </div>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-2'>
                        Status
                      </label>
                      <select
                        value={statusFilter}
                        onChange={e => setStatusFilter(e.target.value)}
                        className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      >
                        <option value='all'>All Status</option>
                        <option value='active'>Active</option>
                        <option value='inactive'>Inactive</option>
                      </select>
                    </div>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-2'>
                        Department
                      </label>
                      <select
                        value={departmentFilter}
                        onChange={e => setDepartmentFilter(e.target.value)}
                        className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      >
                        <option value='all'>All Departments</option>
                        {departments.map(dept => (
                          <option key={dept} value={dept}>{dept}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Enhanced Agents Table */}
            <div className='bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden'>
              <div className='px-8 py-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-gray-100/50'>
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-6'>
                    <div className='flex items-center gap-3'>
                      <div className='w-10 h-10 bg-gray-700 rounded-xl flex items-center justify-center shadow-sm'>
                        <Users className='h-5 w-5 text-white' />
                      </div>
                      <div>
                        <h3 className='text-xl font-bold text-gray-900'>
                          Agents
                        </h3>
                        <p className='text-sm text-gray-600'>
                          Manage and view all agent records
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className='flex items-center gap-3'>
                    <div className='bg-white px-4 py-2 rounded-xl border border-gray-200 shadow-sm'>
                      <span className='text-sm font-medium text-gray-700'>
                        {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

            {/* Department Tabs */}
            <div className='px-8 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-gray-100/30'>
              <nav className='flex space-x-1 overflow-x-auto'>
                <button
                  onClick={() => setActiveDepartmentTab('all')}
                  className={`tab-button px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 flex items-center gap-2 whitespace-nowrap ${
                    activeDepartmentTab === 'all'
                      ? 'bg-gray-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                  }`}
                >
                  <Users className='h-4 w-4' />
                  All Departments
                  <span className='ml-1 px-2 py-0.5 text-xs bg-white/20 rounded-full'>
                    {agents.length}
                  </span>
                </button>
                {departments.map(dept => {
                  const IconComponent = getDepartmentIcon(dept);
                  return (
                    <button
                      key={dept}
                      onClick={() => setActiveDepartmentTab(dept)}
                      className={`tab-button px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 flex items-center gap-2 whitespace-nowrap ${
                        activeDepartmentTab === dept
                          ? 'bg-gray-600 text-white shadow-md'
                          : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                      }`}
                    >
                      <IconComponent className='h-4 w-4' />
                      {dept}
                      <span className='ml-1 px-2 py-0.5 text-xs bg-white/20 rounded-full'>
                        {agents.filter(a => a.department === dept).length}
                      </span>
                    </button>
                  );
                })}
              </nav>
            </div>

        <div className='overflow-x-auto'>
          <table className='min-w-full divide-y divide-gray-200'>
                <thead className='bg-gradient-to-r from-gray-50 to-gray-100/50'>
              <tr>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <Users className='h-3 w-3' />
                  Agent
                      </div>
                </th>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <Mail className='h-3 w-3' />
                  Contact
                      </div>
                </th>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <Building2 className='h-3 w-3' />
                  Role & Department
                      </div>
                </th>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <BarChart3 className='h-3 w-3' />
                  Performance
                      </div>
                </th>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <DollarSign className='h-3 w-3' />
                  Transactions
                      </div>
                </th>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <Activity className='h-3 w-3' />
                  Status
                      </div>
                </th>
                    <th className='px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider'>
                      <div className='flex items-center gap-2'>
                        <MoreHorizontal className='h-3 w-3' />
                  Actions
                      </div>
                </th>
              </tr>
            </thead>
                <tbody className='bg-white divide-y divide-gray-100'>
                  {filteredAgents.map((agent, index) => (
                    <tr
                      key={agent.id}
                      className={`hover:bg-gray-50 transition-all duration-200 group ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'}`}
                    >
                      <td className='px-8 py-5 whitespace-nowrap'>
                    <div className='flex items-center'>
                          <div className='w-12 h-12 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center shadow-sm'>
                            <span className='text-white font-semibold text-sm'>
                          {agent.name
                            .split(' ')
                            .map(n => n[0])
                            .join('')}
                        </span>
                      </div>
                      <div className='ml-4'>
                            <div className='text-sm font-semibold text-gray-900'>
                          {agent.name}
                        </div>
                        <div className='text-sm text-gray-500'>
                          Hired: {new Date(agent.hireDate).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </td>
                      <td className='px-8 py-5 whitespace-nowrap'>
                    <div className='flex items-center space-x-2'>
                      <Mail className='h-4 w-4 text-gray-400' />
                          <span className='text-sm text-gray-900 font-medium'>
                        {agent.email}
                      </span>
                    </div>
                        <div className='flex items-center space-x-2 mt-2'>
                      <Phone className='h-4 w-4 text-gray-400' />
                      <span className='text-sm text-gray-500'>
                        {agent.phone}
                      </span>
                    </div>
                  </td>
                      <td className='px-8 py-5 whitespace-nowrap'>
                        <div className='text-sm font-semibold text-gray-900'>
                      {agent.role}
                    </div>
                    <div className='text-sm text-gray-500'>
                      {agent.department}
                    </div>
                  </td>
                      <td className='px-8 py-5 whitespace-nowrap'>
                    <div className='flex items-center'>
                          <div className='flex-1 bg-gray-200 rounded-full h-2.5 mr-3'>
                            <div
                              className={`h-2.5 rounded-full transition-all duration-300 ${
                                agent.performance >= 90
                                  ? 'bg-green-500'
                                  : agent.performance >= 70
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                              }`}
                          style={{ width: `${agent.performance}%` }}
                        ></div>
                      </div>
                          <span className='text-sm font-semibold text-gray-900 min-w-[3rem]'>
                        {agent.performance}%
                      </span>
                    </div>
                  </td>
                      <td className='px-8 py-5 whitespace-nowrap'>
                        <span className='text-sm font-semibold text-gray-900'>
                          {agent.totalTransactions.toLocaleString()}
                        </span>
                  </td>
                      <td className='px-8 py-5 whitespace-nowrap'>
                    <span
                          className={`inline-flex px-3 py-1 text-xs font-semibold rounded-full ${
                        agent.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                          {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                    </span>
                  </td>
                      <td className='px-8 py-5 whitespace-nowrap text-sm font-medium'>
                        <div className='flex items-center gap-1'>
                          <button className='p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded transition-colors duration-200' title='View Details'>
                            <Eye className='h-3.5 w-3.5' />
                      </button>
                          <button className='p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors duration-200' title='Edit Agent'>
                            <Edit className='h-3.5 w-3.5' />
                      </button>
                          <button className='p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors duration-200' title='Delete Agent'>
                            <Trash2 className='h-3.5 w-3.5' />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAgents.length === 0 && (
              <div className='text-center py-16 px-6'>
                <div className='w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4'>
                  <Users className='h-10 w-10 text-gray-400' />
                </div>
                <h3 className='text-lg font-semibold text-gray-900 mb-2'>
                  {searchTerm || statusFilter !== 'all' || departmentFilter !== 'all' || activeDepartmentTab !== 'all'
                    ? 'No agents found'
                    : 'No agents yet'}
                </h3>
                <p className='text-gray-500 mb-6 max-w-md mx-auto'>
                  {searchTerm || statusFilter !== 'all' || departmentFilter !== 'all' || activeDepartmentTab !== 'all'
                    ? 'Try adjusting your search criteria or filters to find what you\'re looking for.'
                    : 'Start building your team by adding your first agent to the system.'}
                </p>
                <button 
                  onClick={handleAddAgent}
                  className='inline-flex items-center px-6 py-3 border border-transparent rounded-lg text-sm font-medium text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors shadow-sm'
                >
                  <Plus className='h-4 w-4 mr-2' />
                  Add Your First Agent
                </button>
              </div>
            )}

            {/* Table Footer */}
            {filteredAgents.length > 0 && (
              <div className='px-6 py-4 border-t border-gray-100 bg-gray-50'>
                <div className='flex items-center justify-between text-sm text-gray-700'>
                  <span>
                    Showing {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
                  </span>
                  <span className='font-semibold'>
                    Avg Performance: {avgPerformance}%
                  </span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </UnifiedCard>
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className='space-y-6'>
          <div className='bg-white rounded-xl p-6 shadow-sm border border-gray-100'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4'>
              Agent Analytics
            </h3>
            <p className='text-gray-600'>
              Analytics content will be implemented here.
            </p>
          </div>
        </div>
      )}

      {/* Add Agent Modal */}
      {showAddModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'>
          <div className='bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto'>
            <div className='p-6 border-b border-gray-100'>
              <div className='flex items-center justify-between'>
                <h3 className='text-xl font-semibold text-gray-900'>
                  Add New Agent
                </h3>
                <button
                  onClick={handleCloseAddModal}
                  className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200'
                >
                  <X className='h-5 w-5' />
                </button>
              </div>
            </div>
            <div className='p-6 space-y-6'>
              {/* Basic Information */}
              <div className='space-y-4'>
                <h4 className='text-lg font-medium text-gray-900'>Basic Information</h4>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Full Name *
                    </label>
                    <input
                      type='text'
                      value={newAgent.name}
                      onChange={e => handleInputChange('name', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      placeholder='Enter full name'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Email *
                    </label>
                    <input
                      type='email'
                      value={newAgent.email}
                      onChange={e => handleInputChange('email', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      placeholder='Enter email address'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Phone *
                    </label>
                    <input
                      type='tel'
                      value={newAgent.phone}
                      onChange={e => handleInputChange('phone', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      placeholder='Enter phone number'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Start Date *
                    </label>
                    <input
                      type='date'
                      value={newAgent.startDate}
                      onChange={e => handleInputChange('startDate', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                    />
                  </div>
                </div>
              </div>

              {/* Company Information */}
              <div className='space-y-4'>
                <h4 className='text-lg font-medium text-gray-900'>Company Information</h4>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Company Name
                    </label>
                    <input
                      type='text'
                      value={newAgent.companyName}
                      onChange={e => handleInputChange('companyName', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      placeholder='Enter company name'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Nickname
                    </label>
                    <input
                      type='text'
                      value={newAgent.nickname}
                      onChange={e => handleInputChange('nickname', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      placeholder='Enter nickname'
                    />
                  </div>
                </div>
              </div>

              {/* Role and Department */}
              <div className='space-y-4'>
                <h4 className='text-lg font-medium text-gray-900'>Role & Department</h4>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Role *
                    </label>
                    <select
                      value={newAgent.role}
                      onChange={e => handleInputChange('role', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                    >
                      <option value=''>Select role</option>
                      <option value='Senior Agent'>Senior Agent</option>
                      <option value='Agent'>Agent</option>
                      <option value='Junior Agent'>Junior Agent</option>
                      <option value='Team Lead'>Team Lead</option>
                    </select>
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Department *
                    </label>
                    <select
                      value={newAgent.department}
                      onChange={e => handleInputChange('department', e.target.value)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                    >
                      <option value=''>Select department</option>
                      {departments.map(dept => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Financial Information */}
              <div className='space-y-4'>
                <h4 className='text-lg font-medium text-gray-900'>Financial Information</h4>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Salary (₺)
                    </label>
                    <input
                      type='number'
                      value={newAgent.salary}
                      onChange={e => handleInputChange('salary', parseFloat(e.target.value) || 0)}
                      className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors duration-200'
                      placeholder='Enter salary amount'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium text-gray-700 mb-2'>
                      Insurance
                    </label>
                    <div className='flex items-center space-x-4'>
                      <label className='flex items-center'>
                        <input
                          type='radio'
                          name='insurance'
                          checked={newAgent.insurance === true}
                          onChange={() => handleInputChange('insurance', true)}
                          className='h-4 w-4 text-gray-600 focus:ring-gray-500 border-gray-300'
                        />
                        <span className='ml-2 text-sm text-gray-700'>Yes</span>
                      </label>
                      <label className='flex items-center'>
                        <input
                          type='radio'
                          name='insurance'
                          checked={newAgent.insurance === false}
                          onChange={() => handleInputChange('insurance', false)}
                          className='h-4 w-4 text-gray-600 focus:ring-gray-500 border-gray-300'
                        />
                        <span className='ml-2 text-sm text-gray-700'>No</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className='p-6 border-t border-gray-100'>
              <div className='flex gap-3'>
                <button
                  onClick={handleCloseAddModal}
                  className='flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200'
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitAgent}
                  disabled={!newAgent.name || !newAgent.email || !newAgent.phone || !newAgent.startDate || !newAgent.role || !newAgent.department}
                  className='flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
                >
                Add Agent
              </button>
              </div>
            </div>
          </div>
        </div>
        )}
      </div>
    </div>
  );
}
