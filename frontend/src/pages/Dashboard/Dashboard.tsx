import React from 'react';
import { useQuery } from 'react-query';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import {
  ServerIcon,
  CpuChipIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const Dashboard: React.FC = () => {
  const { data: status, isLoading: statusLoading } = useQuery(
    'dashboard-status',
    apiService.getStatus,
    { refetchInterval: 30000 }
  );

  const { data: metrics, isLoading: metricsLoading } = useQuery(
    'dashboard-metrics',
    apiService.getMetrics,
    { refetchInterval: 30000 }
  );

  const { data: chatopsStats, isLoading: chatopsLoading } = useQuery(
    'chatops-statistics',
    apiService.getChatOpsStatistics,
    { refetchInterval: 60000 }
  );

  if (statusLoading || metricsLoading || chatopsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const stats = [
    {
      name: 'System Status',
      value: status?.status || 'Unknown',
      icon: ServerIcon,
      color: status?.status === 'healthy' ? 'text-green-600' : 'text-red-600',
      bgColor: status?.status === 'healthy' ? 'bg-green-50' : 'bg-red-50',
    },
    {
      name: 'CPU Usage',
      value: `${metrics?.cpu_usage || 0}%`,
      icon: CpuChipIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: 'Memory Usage',
      value: `${metrics?.memory_usage || 0}%`,
      icon: ChartBarIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      name: 'Active Alerts',
      value: metrics?.active_alerts || 0,
      icon: ExclamationTriangleIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
  ];

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Dashboard
          </h2>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-8">
        <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((item) => (
            <div
              key={item.name}
              className="relative overflow-hidden rounded-lg bg-white px-4 pb-12 pt-5 shadow sm:px-6 sm:pt-6"
            >
              <dt>
                <div className={`absolute rounded-md p-3 ${item.bgColor}`}>
                  <item.icon className="h-6 w-6 text-gray-600" aria-hidden="true" />
                </div>
                <p className="ml-16 truncate text-sm font-medium text-gray-500">
                  {item.name}
                </p>
              </dt>
              <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
                <p className={`text-2xl font-semibold ${item.color}`}>
                  {item.value}
                </p>
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {/* ChatOps Statistics */}
      {chatopsStats && (
        <div className="mt-8">
          <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
            ChatOps Activity
          </h3>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-indigo-500 rounded-md flex items-center justify-center">
                      <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Commands
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {chatopsStats.total_commands || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                      <ChartBarIcon className="h-5 w-5 text-white" />
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Success Rate
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {chatopsStats.success_rate || 0}%
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                      <CpuChipIcon className="h-5 w-5 text-white" />
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Avg Response Time
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {chatopsStats.avg_response_time || 0}ms
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="mt-8">
        <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
          Recent Activity
        </h3>
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {status?.recent_activity?.slice(0, 5).map((activity: any, index: number) => (
              <li key={index}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-indigo-600 truncate">
                      {activity.action}
                    </p>
                    <div className="ml-2 flex-shrink-0 flex">
                      <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        {activity.status}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        {activity.description}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      <p>
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </li>
            )) || (
              <li>
                <div className="px-4 py-4 sm:px-6">
                  <p className="text-sm text-gray-500">No recent activity</p>
                </div>
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
