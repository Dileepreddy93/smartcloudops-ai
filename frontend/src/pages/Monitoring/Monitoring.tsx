import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import {
  ChartBarIcon,
  DocumentTextIcon,
  ExclaimationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

const Monitoring: React.FC = () => {
  const [activeTab, setActiveTab] = useState('metrics');

  const { data: logs, isLoading: logsLoading } = useQuery(
    'monitoring-logs',
    apiService.getLogs,
    { refetchInterval: 30000 }
  );

  const { data: remediationStatus, isLoading: remediationLoading } = useQuery(
    'remediation-status',
    apiService.getRemediationStatus,
    { refetchInterval: 30000 }
  );

  const { data: integrationStatus, isLoading: integrationLoading } = useQuery(
    'integration-status',
    apiService.getIntegrationStatus,
    { refetchInterval: 30000 }
  );

  const { data: mlHealth, isLoading: mlHealthLoading } = useQuery(
    'ml-health',
    apiService.getMLHealth,
    { refetchInterval: 30000 }
  );

  const tabs = [
    { id: 'metrics', name: 'Metrics', icon: ChartBarIcon },
    { id: 'logs', name: 'Logs', icon: DocumentTextIcon },
    { id: 'remediation', name: 'Remediation', icon: ExclaimationTriangleIcon },
    { id: 'integration', name: 'Integration', icon: CheckCircleIcon },
  ];

  const isLoading = logsLoading || remediationLoading || integrationLoading || mlHealthLoading;

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
            Monitoring
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Monitor system health, logs, and automated remediation
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
        {activeTab === 'metrics' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">System Metrics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <ChartBarIcon className="h-8 w-8 text-blue-500" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">CPU Usage</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {mlHealth?.data?.cpu_usage || 0}%
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <ChartBarIcon className="h-8 w-8 text-green-500" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Memory Usage</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {mlHealth?.data?.memory_usage || 0}%
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <ChartBarIcon className="h-8 w-8 text-purple-500" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Disk Usage</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {mlHealth?.data?.disk_usage || 0}%
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <ChartBarIcon className="h-8 w-8 text-yellow-500" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Network I/O</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {mlHealth?.data?.network_io || 0} MB/s
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">System Logs</h3>
            </div>
            <div className="overflow-hidden">
              <div className="bg-gray-900 text-green-400 p-4 font-mono text-sm h-96 overflow-y-auto">
                {logs?.split('\n').map((log: string, index: number) => (
                  <div key={index} className="mb-1">
                    {log}
                  </div>
                )) || (
                  <div className="text-gray-500">No logs available</div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'remediation' && (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Remediation Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-8 w-8 text-green-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Active Rules</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {remediationStatus?.data?.active_rules || 0}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <ExclaimationTriangleIcon className="h-8 w-8 text-yellow-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Triggered Actions</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {remediationStatus?.data?.triggered_actions || 0}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <XCircleIcon className="h-8 w-8 text-red-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-500">Failed Actions</p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {remediationStatus?.data?.failed_actions || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Remediation Actions</h3>
              <div className="overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Timestamp
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {remediationStatus?.data?.recent_actions?.map((action: any, index: number) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {action.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            action.status === 'success' ? 'bg-green-100 text-green-800' :
                            action.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {action.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(action.timestamp).toLocaleString()}
                        </td>
                      </tr>
                    )) || (
                      <tr>
                        <td colSpan={3} className="px-6 py-4 text-sm text-gray-500 text-center">
                          No recent actions
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'integration' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Integration Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Prometheus</h4>
                <div className="flex items-center">
                  <div className={`h-3 w-3 rounded-full mr-2 ${
                    integrationStatus?.data?.prometheus?.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {integrationStatus?.data?.prometheus?.status || 'disconnected'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                                      {integrationStatus?.data?.prometheus?.endpoint || 'No endpoint configured'}
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Grafana</h4>
                <div className="flex items-center">
                  <div className={`h-3 w-3 rounded-full mr-2 ${
                    integrationStatus?.data?.grafana?.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {integrationStatus?.data?.grafana?.status || 'disconnected'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                                      {integrationStatus?.data?.grafana?.endpoint || 'No endpoint configured'}
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">AWS Services</h4>
                <div className="flex items-center">
                  <div className={`h-3 w-3 rounded-full mr-2 ${
                    integrationStatus?.data?.aws?.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {integrationStatus?.data?.aws?.status || 'disconnected'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                                      {integrationStatus?.data?.aws?.region || 'No region configured'}
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">ML Pipeline</h4>
                <div className="flex items-center">
                  <div className={`h-3 w-3 rounded-full mr-2 ${
                    mlHealth?.data?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                  <span className="text-sm text-gray-600">
                    {mlHealth?.data?.status || 'unhealthy'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                                      Model accuracy: {mlHealth?.data?.model_accuracy || 0}%
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Monitoring;
