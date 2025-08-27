// API Response Types
export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  message: string;
  timestamp: string;
  data?: T;
  error_code?: string;
  details?: any;
}

// Health Check Types
export interface HealthComponent {
  database: boolean;
  ml_service: boolean;
  cache: boolean;
  redis: boolean;
  prometheus: boolean;
}

export interface HealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  components: HealthComponent;
  version?: string;
  uptime_seconds?: number;
}

// ML Prediction Types
export interface MLMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: number;
  load_1m: number;
  load_5m: number;
  load_15m: number;
  response_time: number;
}

export interface MLPrediction {
  is_anomaly: boolean;
  anomaly_score: number;
  confidence: number;
  prediction_timestamp: string;
  model_version: string;
  features_used: string[];
  input_metrics: MLMetrics;
}

export interface MLPredictionRequest {
  metrics: MLMetrics;
}

export interface MLPredictionResponse {
  prediction: MLPrediction;
  input_metrics: MLMetrics;
  model_info: {
    model_type: string;
    model_version: string;
    training_date: string;
    feature_names: string[];
  };
}

// ChatOps Types
export interface ChatOpsRequest {
  query: string;
}

export interface ChatOpsResponse {
  response: string;
  intent?: string;
  confidence?: number;
  entities?: Array<{
    type: string;
    value: string;
    confidence: number;
  }>;
}

// Metrics Types
export interface SystemMetrics {
  cpu: {
    usage_percent: number;
    load_1m: number;
    load_5m: number;
    load_15m: number;
  };
  memory: {
    total_bytes: number;
    used_bytes: number;
    available_bytes: number;
    usage_percent: number;
  };
  disk: {
    total_bytes: number;
    used_bytes: number;
    available_bytes: number;
    usage_percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  system: {
    uptime_seconds: number;
    boot_time: string;
    process_count: number;
  };
}

export interface MetricsResponse {
  metrics: SystemMetrics;
  source: string;
  collection_time: string;
}

// Remediation Types
export interface RemediationAction {
  action: 'scale_up' | 'scale_down' | 'restart_service' | 'clear_cache' | 'backup_data';
  target: string;
  parameters?: Record<string, any>;
}

export interface RemediationResponse {
  action: string;
  success: boolean;
  details?: {
    message: string;
    affected_resources: string[];
    execution_log: string[];
  };
  execution_time_seconds: number;
}

// Authentication Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    role: string;
    permissions: string[];
  };
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  created_at: string;
  last_login: string;
}

// API Key Types
export interface ApiKey {
  key_id: string;
  role: string;
  permissions: string[];
  key_preview: string;
  created_at: string;
  last_used?: string;
  is_active: boolean;
}

// Dashboard Types
export interface DashboardStats {
  system_status: string;
  active_alerts: number;
  total_requests: number;
  ml_predictions: number;
  uptime_percentage: number;
}

export interface Alert {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  source: string;
  timestamp: string;
  resolved: boolean;
  resolved_at?: string;
}

// Error Types
export interface ApiError {
  message: string;
  error_code: string;
  details?: any;
  request_id?: string;
}

// Rate Limiting Types
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
  window: number;
  client_id: string;
}

// Pagination Types
export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
  links: {
    self: string;
    first: string;
    last: string;
    next?: string;
    prev?: string;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}

// Monitoring Types
export interface MonitoringData {
  metrics: SystemMetrics;
  alerts: Alert[];
  predictions: MLPrediction[];
  remediations: RemediationResponse[];
}

// Admin Types
export interface AdminStats {
  total_users: number;
  active_api_keys: number;
  total_requests_24h: number;
  ml_predictions_24h: number;
  system_health: HealthResponse;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'metrics_update' | 'alert' | 'prediction' | 'remediation' | 'health_check';
  data: any;
  timestamp: string;
}

// Configuration Types
export interface AppConfig {
  api_base_url: string;
  websocket_url: string;
  refresh_interval: number;
  max_retries: number;
  timeout: number;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'checkbox';
  required: boolean;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
  options?: Array<{
    value: string;
    label: string;
  }>;
}

export interface FormData {
  [key: string]: any;
}

// Component Props Types
export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export interface ErrorDisplayProps {
  error: ApiError;
  onRetry?: () => void;
  showDetails?: boolean;
}

export interface StatusBadgeProps {
  status: string;
  className?: string;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon?: React.ComponentType<any>;
  className?: string;
}

// Hook Types
export interface UseApiOptions {
  enabled?: boolean;
  refetchInterval?: number;
  retry?: number;
  retryDelay?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError) => void;
}

export interface UseApiResult<T> {
  data: T | undefined;
  isLoading: boolean;
  error: ApiError | null;
  refetch: () => void;
  isRefetching: boolean;
}
