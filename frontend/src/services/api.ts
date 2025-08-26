import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import toast from 'react-hot-toast';

// Create axios instance with base configuration
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
      toast.error('Session expired. Please login again.');
    } else if (error.response?.status === 403) {
      toast.error('Access denied. Insufficient permissions.');
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.');
    } else {
      const message = error.response?.data?.error || 'An error occurred';
      toast.error(message);
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Authentication
  auth: {
    login: '/auth/login',
    verify: '/auth/verify',
  },
  
  // Dashboard
  dashboard: {
    status: '/status',
    metrics: '/metrics',
  },
  
  // ChatOps
  chatops: {
    process: '/api/v1/chatops/process',
    intents: '/api/v1/chatops/intents',
    history: '/api/v1/chatops/history',
    statistics: '/api/v1/chatops/statistics',
    execute: '/api/v1/chatops/execute',
    executions: '/api/v1/chatops/executions',
    health: '/api/v1/chatops/health',
    test: '/api/v1/chatops/test',
    safetyLimits: '/api/v1/chatops/safety-limits',
  },
  
  // ML
  ml: {
    health: '/ml/health',
    predict: '/ml/predict',
    metrics: '/ml/metrics',
  },
  
  // Monitoring
  monitoring: {
    logs: '/logs',
    remediation: {
      status: '/api/v1/remediation/status',
      test: '/api/v1/remediation/test',
      rules: '/api/v1/remediation/rules',
    },
    integration: {
      status: '/api/v1/integration/status',
      start: '/api/v1/integration/start',
      health: '/api/v1/integration/health',
    },
  },
};

// API service functions
export const apiService = {
  // Authentication
  login: async (username: string, password: string) => {
    const response = await api.post(endpoints.auth.login, { username, password });
    return response.data;
  },
  
  verifyToken: async (token: string) => {
    const response = await api.post(endpoints.auth.verify, { token });
    return response.data;
  },
  
  // Dashboard
  getStatus: async () => {
    const response = await api.get(endpoints.dashboard.status);
    return response.data;
  },
  
  getMetrics: async () => {
    const response = await api.get(endpoints.dashboard.metrics);
    return response.data;
  },
  
  // ChatOps
  processChatOpsCommand: async (command: string, userId?: string, channel?: string) => {
    const response = await api.post(endpoints.chatops.process, {
      command,
      user_id: userId,
      channel,
    });
    return response.data;
  },
  
  getSupportedIntents: async () => {
    const response = await api.get(endpoints.chatops.intents);
    return response.data;
  },
  
  getCommandHistory: async (limit: number = 10) => {
    const response = await api.get(`${endpoints.chatops.history}?limit=${limit}`);
    return response.data;
  },
  
  getChatOpsStatistics: async () => {
    const response = await api.get(endpoints.chatops.statistics);
    return response.data;
  },
  
  executeAction: async (action: string, parameters: any) => {
    const response = await api.post(endpoints.chatops.execute, {
      action,
      parameters,
    });
    return response.data;
  },
  
  getExecutionHistory: async (limit: number = 10) => {
    const response = await api.get(`${endpoints.chatops.executions}?limit=${limit}`);
    return response.data;
  },
  
  getChatOpsHealth: async () => {
    const response = await api.get(endpoints.chatops.health);
    return response.data;
  },
  
  testCommand: async (command: string) => {
    const response = await api.post(endpoints.chatops.test, { command });
    return response.data;
  },
  
  getSafetyLimits: async () => {
    const response = await api.get(endpoints.chatops.safetyLimits);
    return response.data;
  },
  
  updateSafetyLimits: async (limits: any) => {
    const response = await api.put(endpoints.chatops.safetyLimits, limits);
    return response.data;
  },
  
  // ML
  getMLHealth: async () => {
    const response = await api.get(endpoints.ml.health);
    return response.data;
  },
  
  predictAnomaly: async (metrics: any) => {
    const response = await api.post(endpoints.ml.predict, { metrics });
    return response.data;
  },
  
  getMLMetrics: async () => {
    const response = await api.get(endpoints.ml.metrics);
    return response.data;
  },
  
  // Monitoring
  getLogs: async () => {
    const response = await api.get(endpoints.monitoring.logs);
    return response.data;
  },
  
  getRemediationStatus: async () => {
    const response = await api.get(endpoints.monitoring.remediation.status);
    return response.data;
  },
  
  testRemediation: async (metrics: any) => {
    const response = await api.post(endpoints.monitoring.remediation.test, { metrics });
    return response.data;
  },
  
  getRemediationRules: async () => {
    const response = await api.get(endpoints.monitoring.remediation.rules);
    return response.data;
  },
  
  addRemediationRule: async (rule: any) => {
    const response = await api.post(endpoints.monitoring.remediation.rules, rule);
    return response.data;
  },
  
  getIntegrationStatus: async () => {
    const response = await api.get(endpoints.monitoring.integration.status);
    return response.data;
  },
  
  startIntegration: async () => {
    const response = await api.post(endpoints.monitoring.integration.start);
    return response.data;
  },
  
  getIntegrationHealth: async () => {
    const response = await api.get(endpoints.monitoring.integration.health);
    return response.data;
  },
};

export { api };
