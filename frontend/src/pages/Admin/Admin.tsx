import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  Cog6ToothIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

const Admin: React.FC = () => {
  const [activeTab, setActiveTab] = useState('system');
  const queryClient = useQueryClient();

  const { data: safetyLimits, isLoading: safetyLoading } = useQuery(
    'safety-limits',
    apiService.getSafetyLimits
  );

  const { data: remediationRules, isLoading: rulesLoading } = useQuery(
    'remediation-rules',
    apiService.getRemediationRules
  );

  const { data: integrationHealth, isLoading: healthLoading } = useQuery(
    'integration-health',
    apiService.getIntegrationHealth
  );

  const updateSafetyLimitsMutation = useMutation(
    (limits: any) => apiService.updateSafetyLimits(limits),
    {
      onSuccess: () => {
        toast.success('Safety limits updated successfully');
        queryClient.invalidateQueries('safety-limits');
      },
      onError: () => {
        toast.error('Failed to update safety limits');
      },
    }
  );

  const addRemediationRuleMutation = useMutation(
    (rule: any) => apiService.addRemediationRule(rule),
    {
      onSuccess: () => {
        toast.success('Remediation rule added successfully');
        queryClient.invalidateQueries('remediation-rules');
      },
      onError: () => {
        toast.error('Failed to add remediation rule');
      },
    }
  );

  const startIntegrationMutation = useMutation(
    () => apiService.startIntegration(),
    {
      onSuccess: () => {
        toast.success('Integration started successfully');
        queryClient.invalidateQueries('integration-health');
      },
      onError: () => {
        toast.error('Failed to start integration');
      },
    }
  );

  const tabs = [
    { id: 'system', name: 'System Config', icon: Cog6ToothIcon },
    { id: 'users', name: 'User Management', icon: UserGroupIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'analytics', name: 'Analytics', icon: ChartBarIcon },
  ];

  const isLoading = safetyLoading || rulesLoading || healthLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Admin Panel
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage system configuration, users, and security settings
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'system' && (
          <div className="space-y-6">
            {/* Safety Limits */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Safety Limits</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max CPU Usage (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={safetyLimits?.data?.max_cpu_usage || 90}
                    onChange={(e) => {
                      const newLimits = {
                        ...safetyLimits?.data,
                        max_cpu_usage: parseInt(e.target.value),
                      };
                      updateSafetyLimitsMutation.mutate(newLimits);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Memory Usage (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={safetyLimits?.data?.max_memory_usage || 85}
                    onChange={(e) => {
                      const newLimits = {
                        ...safetyLimits?.data,
                        max_memory_usage: parseInt(e.target.value),
                      };
                      updateSafetyLimitsMutation.mutate(newLimits);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Disk Usage (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={safetyLimits?.data?.max_disk_usage || 80}
                    onChange={(e) => {
                      const newLimits = {
                        ...safetyLimits?.data,
                        max_disk_usage: parseInt(e.target.value),
                      };
                      updateSafetyLimitsMutation.mutate(newLimits);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Concurrent Actions
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={safetyLimits?.data?.max_concurrent_actions || 5}
                    onChange={(e) => {
                      const newLimits = {
                        ...safetyLimits?.data,
                        max_concurrent_actions: parseInt(e.target.value),
                      };
                      updateSafetyLimitsMutation.mutate(newLimits);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>

            {/* Integration Management */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Integration Management</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">System Integration</h4>
                    <p className="text-sm text-gray-500">
                      Status: {integrationHealth?.data?.status || 'unknown'}
                    </p>
                  </div>
                  <button
                    onClick={() => startIntegrationMutation.mutate()}
                    disabled={startIntegrationMutation.isLoading}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                  >
                    {startIntegrationMutation.isLoading ? 'Starting...' : 'Start Integration'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">User Management</h3>
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Current Users</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">admin</p>
                      <p className="text-sm text-gray-500">Administrator</p>
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                      Active
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">API Keys</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Admin API Key</p>
                      <p className="text-sm text-gray-500">Full system access</p>
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      Active
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">ML API Key</p>
                      <p className="text-sm text-gray-500">ML operations only</p>
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      Active
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Read-only API Key</p>
                      <p className="text-sm text-gray-500">Read access only</p>
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      Active
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Security Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">JWT Authentication</h4>
                    <p className="text-sm text-gray-500">Token-based authentication system</p>
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Enabled
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">API Key Authentication</h4>
                    <p className="text-sm text-gray-500">API key-based access control</p>
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Enabled
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">Rate Limiting</h4>
                    <p className="text-sm text-gray-500">Request rate limiting protection</p>
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Enabled
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">Input Validation</h4>
                    <p className="text-sm text-gray-500">Request input sanitization</p>
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Enabled
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Audit Log</h3>
              <div className="bg-gray-900 text-green-400 p-4 font-mono text-sm h-64 overflow-y-auto rounded">
                <div className="mb-1">
                  <span className="text-gray-500">[2024-01-15 10:30:15]</span>{' '}
                  <span className="text-blue-400">[INFO]</span> User admin logged in successfully
                </div>
                <div className="mb-1">
                  <span className="text-gray-500">[2024-01-15 10:25:42]</span>{' '}
                  <span className="text-blue-400">[INFO]</span> Safety limits updated
                </div>
                <div className="mb-1">
                  <span className="text-gray-500">[2024-01-15 10:20:18]</span>{' '}
                  <span className="text-yellow-400">[WARNING]</span> High CPU usage detected
                </div>
                <div className="mb-1">
                  <span className="text-gray-500">[2024-01-15 10:15:33]</span>{' '}
                  <span className="text-green-400">[SUCCESS]</span> Remediation action completed
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">System Analytics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-8 w-8 text-blue-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Total Commands</p>
                      <p className="text-2xl font-semibold text-gray-900">1,247</p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-8 w-8 text-green-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Success Rate</p>
                      <p className="text-2xl font-semibold text-gray-900">94.2%</p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-8 w-8 text-purple-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Avg Response</p>
                      <p className="text-2xl font-semibold text-gray-900">1.2s</p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <ChartBarIcon className="h-8 w-8 text-yellow-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Uptime</p>
                      <p className="text-2xl font-semibold text-gray-900">99.8%</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>CPU Usage</span>
                    <span>65%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '65%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Memory Usage</span>
                    <span>78%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '78%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Disk Usage</span>
                    <span>45%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-purple-600 h-2 rounded-full" style={{ width: '45%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
