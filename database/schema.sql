-- SmartCloudOps AI - Production Database Schema
-- =============================================
-- Complete database schema with proper constraints, indexes, and relationships

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS anomaly_predictions CASCADE;
DROP TABLE IF EXISTS model_predictions CASCADE;
DROP TABLE IF EXISTS api_key_usage CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS ml_model_versions CASCADE;
DROP TABLE IF EXISTS ml_models CASCADE;
DROP TABLE IF EXISTS metrics CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table for authentication and auditing
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Metrics table for system monitoring data
CREATE TABLE metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(100) NOT NULL,
    -- CPU metrics with proper constraints
    cpu_usage DECIMAL(5,2) NOT NULL CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
    -- Memory metrics with proper constraints  
    memory_usage DECIMAL(5,2) NOT NULL CHECK (memory_usage >= 0 AND memory_usage <= 100),
    -- Disk metrics with proper constraints
    disk_usage DECIMAL(5,2) NOT NULL CHECK (disk_usage >= 0 AND disk_usage <= 100),
    -- System load metrics
    load_1m DECIMAL(8,4) NOT NULL CHECK (load_1m >= 0),
    load_5m DECIMAL(8,4) NOT NULL CHECK (load_5m >= 0),
    load_15m DECIMAL(8,4) CHECK (load_15m >= 0),
    -- I/O metrics (bytes per second)
    disk_io_read BIGINT NOT NULL CHECK (disk_io_read >= 0),
    disk_io_write BIGINT NOT NULL CHECK (disk_io_write >= 0),
    -- Network metrics (bytes per second)
    network_rx BIGINT NOT NULL CHECK (network_rx >= 0),
    network_tx BIGINT NOT NULL CHECK (network_tx >= 0),
    -- Application metrics
    response_time DECIMAL(10,3) NOT NULL CHECK (response_time >= 0),
    error_rate DECIMAL(5,2) CHECK (error_rate >= 0 AND error_rate <= 100),
    -- Anomaly detection
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_score DECIMAL(5,4) CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- ML Models table for model management
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL CHECK (model_type IN ('isolation_forest', 'prophet', 'rule_based', 'ensemble')),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(model_name)
);

-- ML Model Versions for proper version control
CREATE TABLE ml_model_versions (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    training_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    training_data_start TIMESTAMP WITH TIME ZONE NOT NULL,
    training_data_end TIMESTAMP WITH TIME ZONE NOT NULL,
    training_data_size INTEGER NOT NULL CHECK (training_data_size > 0),
    -- Model configuration and thresholds
    model_config JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    -- Performance metrics
    accuracy DECIMAL(5,4) CHECK (accuracy >= 0 AND accuracy <= 1),
    precision_score DECIMAL(5,4) CHECK (precision_score >= 0 AND precision_score <= 1),
    recall_score DECIMAL(5,4) CHECK (recall_score >= 0 AND recall_score <= 1),
    f1_score DECIMAL(5,4) CHECK (f1_score >= 0 AND f1_score <= 1),
    -- Model artifacts (S3 paths or local paths)
    model_path VARCHAR(500),
    scaler_path VARCHAR(500),
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'training' CHECK (status IN ('training', 'ready', 'deployed', 'deprecated')),
    is_deployed BOOLEAN NOT NULL DEFAULT FALSE,
    deployment_notes TEXT,
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    UNIQUE(model_id, version)
);

-- API Keys table for authentication
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    permissions TEXT[] NOT NULL,
    user_id UUID REFERENCES users(id),
    description TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count BIGINT NOT NULL DEFAULT 0,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- API Key Usage tracking for monitoring and rate limiting
CREATE TABLE api_key_usage (
    id BIGSERIAL PRIMARY KEY,
    api_key_id INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Model Predictions for tracking and analysis
CREATE TABLE model_predictions (
    id BIGSERIAL PRIMARY KEY,
    model_version_id INTEGER NOT NULL REFERENCES ml_model_versions(id),
    metrics_id BIGINT REFERENCES metrics(id),
    predicted_anomaly BOOLEAN NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    prediction_time_ms INTEGER NOT NULL CHECK (prediction_time_ms >= 0),
    model_features JSONB,
    actual_anomaly BOOLEAN, -- For feedback learning
    feedback_provided_at TIMESTAMP WITH TIME ZONE,
    feedback_provided_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Anomaly Predictions summary for faster queries
CREATE TABLE anomaly_predictions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source VARCHAR(100) NOT NULL,
    anomaly_detected BOOLEAN NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence_score DECIMAL(5,4) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    alert_sent BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance optimization
-- Metrics table indexes
CREATE INDEX idx_metrics_timestamp ON metrics (timestamp DESC);
CREATE INDEX idx_metrics_source_time ON metrics (source, timestamp DESC);
CREATE INDEX idx_metrics_anomaly ON metrics (is_anomaly, timestamp DESC) WHERE is_anomaly = TRUE;
CREATE INDEX idx_metrics_created_at ON metrics (created_at DESC);
CREATE INDEX idx_metrics_cpu_usage ON metrics (cpu_usage) WHERE cpu_usage > 80;
CREATE INDEX idx_metrics_memory_usage ON metrics (memory_usage) WHERE memory_usage > 80;

-- Composite index for time-series queries
CREATE INDEX idx_metrics_timeseries ON metrics (source, timestamp DESC, cpu_usage, memory_usage, is_anomaly);

-- ML Models indexes
CREATE INDEX idx_ml_models_active ON ml_models (is_active, created_at DESC);
CREATE INDEX idx_ml_model_versions_deployed ON ml_model_versions (is_deployed, model_id);
CREATE INDEX idx_ml_model_versions_status ON ml_model_versions (status, created_at DESC);

-- API Keys indexes
CREATE INDEX idx_api_keys_hash ON api_keys (key_hash);
CREATE INDEX idx_api_keys_user ON api_keys (user_id, is_active);
CREATE INDEX idx_api_keys_active ON api_keys (is_active, expires_at);

-- API Usage indexes for analytics
CREATE INDEX idx_api_usage_key_time ON api_key_usage (api_key_id, created_at DESC);
CREATE INDEX idx_api_usage_endpoint ON api_key_usage (endpoint, created_at DESC);
CREATE INDEX idx_api_usage_time ON api_key_usage (created_at DESC);

-- Predictions indexes
CREATE INDEX idx_predictions_model_time ON model_predictions (model_version_id, created_at DESC);
CREATE INDEX idx_predictions_anomaly ON model_predictions (predicted_anomaly, created_at DESC);
CREATE INDEX idx_anomaly_predictions_time ON anomaly_predictions (timestamp DESC);
CREATE INDEX idx_anomaly_predictions_unack ON anomaly_predictions (acknowledged, severity, timestamp DESC) WHERE acknowledged = FALSE;

-- Partitioning for large tables (PostgreSQL 10+)
-- Partition metrics table by month for better performance
CREATE TABLE metrics_y2025m08 PARTITION OF metrics
FOR VALUES FROM ('2025-08-01 00:00:00+00') TO ('2025-09-01 00:00:00+00');

CREATE TABLE metrics_y2025m09 PARTITION OF metrics
FOR VALUES FROM ('2025-09-01 00:00:00+00') TO ('2025-10-01 00:00:00+00');

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW active_models AS
SELECT 
    m.model_name,
    mv.version,
    mv.accuracy,
    mv.f1_score,
    mv.is_deployed,
    mv.created_at as version_created_at,
    u.username as created_by_username
FROM ml_models m
JOIN ml_model_versions mv ON m.id = mv.model_id
JOIN users u ON mv.created_by = u.id
WHERE m.is_active = TRUE
ORDER BY mv.created_at DESC;

CREATE VIEW recent_anomalies AS
SELECT 
    timestamp,
    source,
    cpu_usage,
    memory_usage,
    disk_usage,
    response_time,
    anomaly_score,
    created_at
FROM metrics 
WHERE is_anomaly = TRUE 
AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Materialized view for analytics dashboard
CREATE MATERIALIZED VIEW hourly_metrics_summary AS
SELECT 
    date_trunc('hour', timestamp) as hour,
    source,
    COUNT(*) as total_metrics,
    AVG(cpu_usage) as avg_cpu,
    MAX(cpu_usage) as max_cpu,
    AVG(memory_usage) as avg_memory,
    MAX(memory_usage) as max_memory,
    AVG(response_time) as avg_response_time,
    COUNT(*) FILTER (WHERE is_anomaly = TRUE) as anomaly_count,
    AVG(anomaly_score) FILTER (WHERE is_anomaly = TRUE) as avg_anomaly_score
FROM metrics
GROUP BY date_trunc('hour', timestamp), source
ORDER BY hour DESC, source;

-- Create index on materialized view
CREATE INDEX idx_hourly_summary_time_source ON hourly_metrics_summary (hour DESC, source);

-- Initial data setup
-- Create default admin user
INSERT INTO users (username, email, role) VALUES 
('admin', 'admin@smartcloudops.ai', 'admin'),
('system', 'system@smartcloudops.ai', 'admin');

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO smartcloudops;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO smartcloudops;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO smartcloudops;

-- Comments for documentation
COMMENT ON TABLE metrics IS 'System monitoring metrics with proper data types and constraints';
COMMENT ON TABLE ml_models IS 'ML model definitions and metadata';
COMMENT ON TABLE ml_model_versions IS 'Version control for ML models with performance tracking';
COMMENT ON TABLE api_keys IS 'API key management with usage tracking and rate limiting';
COMMENT ON TABLE users IS 'User management for authentication and auditing';

COMMENT ON COLUMN metrics.timestamp IS 'Metric collection timestamp in UTC';
COMMENT ON COLUMN metrics.is_anomaly IS 'Boolean flag indicating if this metric represents an anomaly';
COMMENT ON COLUMN metrics.anomaly_score IS 'Anomaly confidence score between 0 and 1';
COMMENT ON COLUMN ml_model_versions.f1_score IS 'F1 score for model performance evaluation';
