import React from 'react';
import { useQuery } from 'react-query';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import {
  ServerIcon,
  CpuChipIcon,
  ChartBarIcon,
  ExclaimationTriangleIcon,
} from '@heroicons/react/24/outline';

const Dashboard: React.FC = () => {
  const { 
    data: status, 
    isLoading: statusLoading, 
    error: statusError,
    refetch: refetchStatus 
  } = useQuery(
    'dashboard-status',
    apiService.getStatus,
    { 
      refetchInterval: 30000,
      retry: 3,
      retryDelay: 1000
    }
  );

  const { 
    data: metrics, 
    isLoading: metricsLoading, 
    error: metricsError,
    refetch: refetchMetrics 
  } = useQuery(
    'dashboard-metrics',
    apiService.getMetrics,
    { 
      refetchInterval: 30000,
      retry: 3,
      retryDelay: 1000
    }
  );

  const { 
    data: chatopsStats, 
    isLoading: chatopsLoading, 
    error: chatopsError,
    refetch: refetchChatOps 
  } = useQuery(
    'chatops-statistics',
    apiService.getChatOpsStatistics,
    { 
      refetchInterval: 60000,
      retry: 3,
      retryDelay: 1000
    }
  );

  // Handle loading state
  if (statusLoading || metricsLoading || chatopsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Loading dashboard data..." />
      </div>
    );
  }

  // Handle error state
  if (statusError || metricsError || chatopsError) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="text-center">
                          <ExclaimationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Error Loading Dashboard
          </h3>
          <p className="text-gray-600 mb-4">
            There was an error loading the dashboard data. Please try again.
          </p>
          <button
            onClick={() => {
              refetchStatus();
              refetchMetrics();
              refetchChatOps();
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
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
              icon: ExclaimationTriangleIcon,
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
          <p className="mt-1 text-sm text-gray-500">
            Real-time system monitoring and metrics
          </p>
        </div>
        <div className="mt-4 flex md:ml-4 md:mt-0">
          <button
            onClick={() => {
              refetchStatus();
              refetchMetrics();
              refetchChatOps();
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
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

      {/* Additional dashboard content can be added here */}
    </div>
  );
};

export default Dashboard;
