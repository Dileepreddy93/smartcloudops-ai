import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { toast } from 'react-hot-toast';

// API Response Types
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
  error_code?: string;
}

export interface SystemStatus {
  status: string;
  message: string;
  timestamp: string;
  version: string;
  services: {
    ml_service: string;
    model_loaded: boolean;
  };
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: number;
  response_time: number;
  error_rate: number;
  request_count: number;
  active_alerts: number;
}

export interface ChatOpsStatistics {
  total_commands: number;
  success_rate: number;
  avg_response_time: number;
  recent_commands: Array<{
    command: string;
    response: string;
    timestamp: string;
    success: boolean;
  }>;
}

export interface MLPrediction {
  anomaly_score: number;
  is_anomaly: boolean;
  confidence: number;
  model_version: string;
  features_used: string[];
  threshold: number;
  timestamp: string;
}

// API Service Class
class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for authentication
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
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
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error: AxiosError) => {
        this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private handleApiError(error: AxiosError): void {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;

      switch (status) {
        case 401:
          toast.error('Authentication required. Please log in.');
          // Redirect to login
          window.location.href = '/login';
          break;
        case 403:
          toast.error('Access denied. Insufficient permissions.');
          break;
        case 404:
          toast.error('Resource not found.');
          break;
        case 429:
          toast.error('Too many requests. Please try again later.');
          break;
        case 500:
          toast.error('Server error. Please try again later.');
          break;
        default:
          toast.error(data?.message || 'An unexpected error occurred.');
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
    } else {
      toast.error('An unexpected error occurred.');
    }
  }

  async makeRequest<T>(
    method: 'get' | 'post' | 'put' | 'delete',
    url: string,
    data?: any,
    retries: number = 3
  ): Promise<T> {
    try {
      const response = await this.api[method](url, data);
      return response.data;
    } catch (error) {
      if (retries > 0 && this.isRetryableError(error as AxiosError)) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.makeRequest(method, url, data, retries - 1);
      }
      throw error;
    }
  }

  private isRetryableError(error: AxiosError): boolean {
    return (
      !error.response ||
      (error.response.status >= 500 && error.response.status < 600) ||
      error.response.status === 429
    );
  }

  // Health and Status
  async getStatus(): Promise<SystemStatus> {
    return this.makeRequest<SystemStatus>('get', '/status');
  }

  async getHealth(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/health');
  }

  // Metrics
  async getMetrics(): Promise<SystemMetrics> {
    return this.makeRequest<SystemMetrics>('get', '/metrics');
  }

  // ChatOps
  async getChatOpsStatistics(): Promise<ChatOpsStatistics> {
    return this.makeRequest<ChatOpsStatistics>('get', '/chatops/statistics');
  }

  async processChatOpsCommand(command: string): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('post', '/query', { command });
  }

  // ML Predictions
  async predictAnomaly(metrics: Partial<SystemMetrics>): Promise<MLPrediction> {
    return this.makeRequest<MLPrediction>('post', '/ml/predict', { metrics });
  }

  async getMLHealth(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/ml/health');
  }

  async getModelInfo(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/ml/model-info');
  }

  // Logs
  async getLogs(): Promise<string> {
    return this.makeRequest<string>('get', '/logs');
  }

  // Authentication
  async login(username: string, password: string): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('post', '/auth/login', {
      username,
      password,
    });
  }

  async logout(): Promise<void> {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  }

  // Admin methods
  async getSafetyLimits(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/admin/safety-limits');
  }

  async updateSafetyLimits(limits: any): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('put', '/admin/safety-limits', limits);
  }

  async getRemediationRules(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/admin/remediation-rules');
  }

  async addRemediationRule(rule: any): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('post', '/admin/remediation-rules', rule);
  }

  async getIntegrationHealth(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/admin/integration-health');
  }

  async startIntegration(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('post', '/admin/integration/start');
  }

  async getRemediationStatus(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/remediation/status');
  }

  async getIntegrationStatus(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/integration/status');
  }

  // ChatOps methods
  async getSupportedIntents(): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', '/chatops/intents');
  }

  async getCommandHistory(limit: number = 20): Promise<ApiResponse> {
    return this.makeRequest<ApiResponse>('get', `/chatops/history?limit=${limit}`);
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem('authToken');
  }

  getAuthToken(): string | null {
    return localStorage.getItem('authToken');
  }

  setAuthToken(token: string): void {
    localStorage.setItem('authToken', token);
  }
}

// Export singleton instance
export const apiService = new ApiService();
