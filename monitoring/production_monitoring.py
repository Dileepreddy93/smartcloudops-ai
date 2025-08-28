#!/usr/bin/env python3
"""
Production Monitoring & Alerting System
=======================================

Comprehensive monitoring solution including:
- Prometheus metrics collection
- Grafana dashboard configuration
- Alerting rules and notifications
- Performance monitoring
- Error tracking and alerting
- Custom business metrics
"""


import os
import logging
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from prometheus_client import (
    Counter, Gauge, Histogram, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, push_to_gateway
)

from flask import Flask, Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str
    severity: str  # 'critical', 'warning', 'info'
    duration: str  # Prometheus duration string
    summary: str
    description: str
    labels: Dict[str, str]

class ProductionMetrics:
    """Production metrics collection and management."""
    
    def __init__(self):
        # Create custom registry
        self.registry = CollectorRegistry()
        
        # Application metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.http_request_size_bytes = Histogram(
            'http_request_size_bytes',
            'HTTP request size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.http_response_size_bytes = Histogram(
            'http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Business metrics
        self.ml_predictions_total = Counter(
            'ml_predictions_total',
            'Total ML predictions',
            ['model_version', 'prediction_type'],
            registry=self.registry
        )
        
        self.ml_prediction_duration_seconds = Histogram(
            'ml_prediction_duration_seconds',
            'ML prediction duration in seconds',
            ['model_version'],
            registry=self.registry
        )
        
        self.anomaly_detection_rate = Gauge(
            'anomaly_detection_rate',
            'Current anomaly detection rate',
            ['model_version'],
            registry=self.registry
        )
        
        # System metrics
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            registry=self.registry
        )
        
        self.redis_connections_active = Gauge(
            'redis_connections_active',
            'Active Redis connections',
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['type', 'component'],
            registry=self.registry
        )
        
        self.error_rate = Gauge(
            'error_rate',
            'Current error rate',
            ['component'],
            registry=self.registry
        )
        
        # Performance metrics
        self.memory_usage_bytes = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.cpu_usage_percent = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Custom business metrics
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.api_rate_limit_hits = Counter(
            'api_rate_limit_hits',
            'API rate limit hits',
            ['endpoint', 'user_id'],
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, 
                          status_code: int, duration: float,
                          request_size: int = 0, response_size: int = 0):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status=status_code
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            self.http_request_size_bytes.labels(
                method=method, 
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size > 0:
            self.http_response_size_bytes.labels(
                method=method, 
                endpoint=endpoint
            ).observe(response_size)
    
    def record_ml_prediction(self, model_version: str, prediction_type: str, 
                           duration: float, is_anomaly: bool):
        """Record ML prediction metrics."""
        self.ml_predictions_total.labels(
            model_version=model_version,
            prediction_type=prediction_type
        ).inc()
        
        self.ml_prediction_duration_seconds.labels(
            model_version=model_version
        ).observe(duration)
        
        # Update anomaly detection rate
        if is_anomaly:
            self.anomaly_detection_rate.labels(
                model_version=model_version
            ).set(1.0)
        else:
            self.anomaly_detection_rate.labels(
                model_version=model_version
            ).set(0.0)
    
    def record_database_operation(self, operation: str, duration: float, 
                                connections: int):
        """Record database operation metrics."""
        self.database_query_duration_seconds.labels(
            operation=operation
        ).observe(duration)
        
        self.database_connections_active.set(connections)
    
    def record_redis_operation(self, connections: int, hit_ratio: float):
        """Record Redis operation metrics."""
        self.redis_connections_active.set(connections)
        self.cache_hit_ratio.set(hit_ratio)
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics."""
        self.errors_total.labels(
            type=error_type,
            component=component
        ).inc()
    
    def record_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Record system metrics."""
        self.memory_usage_bytes.set(memory_bytes)
        self.cpu_usage_percent.set(cpu_percent)
    
    def record_business_metrics(self, active_users: int):
        """Record business metrics."""
        self.active_users.set(active_users)
    
    def record_rate_limit_hit(self, endpoint: str, user_id: str):
        """Record API rate limit hits."""
        self.api_rate_limit_hits.labels(
            endpoint=endpoint,
            user_id=user_id
        ).inc()

class AlertManager:
    """Alert management and notification system."""
    
    def __init__(self):
        self.alert_rules = self._load_alert_rules()
        self.alert_history = []
        self.notification_channels = self._setup_notification_channels()
    
    def _load_alert_rules(self) -> List[AlertRule]:
        """Load alert rules from configuration."""
        return [
            AlertRule(
                name="HighErrorRate",
                condition="rate(errors_total[5m]) > 0.1",
                severity="critical",
                duration="5m",
                summary="High error rate detected",
                description="Error rate is above 10% for the last 5 minutes",
                labels={"severity": "critical"}
            ),
            AlertRule(
                name="HighResponseTime",
                condition="histogram_quantile(0.95, http_request_duration_seconds) > 1",
                severity="warning",
                duration="5m",
                summary="High response time detected",
                description="95th percentile response time is above 1 second",
                labels={"severity": "warning"}
            ),
            AlertRule(
                name="HighCPUUsage",
                condition="cpu_usage_percent > 80",
                severity="warning",
                duration="5m",
                summary="High CPU usage detected",
                description="CPU usage is above 80%",
                labels={"severity": "warning"}
            ),
            AlertRule(
                name="HighMemoryUsage",
                condition="memory_usage_bytes / 1024 / 1024 / 1024 > 8",
                severity="warning",
                duration="5m",
                summary="High memory usage detected",
                description="Memory usage is above 8GB",
                labels={"severity": "warning"}
            ),
            AlertRule(
                name="DatabaseConnectionIssues",
                condition="database_connections_active == 0",
                severity="critical",
                duration="1m",
                summary="Database connection issues",
                description="No active database connections",
                labels={"severity": "critical"}
            ),
            AlertRule(
                name="MLPipelineFailure",
                condition="rate(ml_predictions_total[5m]) == 0",
                severity="critical",
                duration="5m",
                summary="ML pipeline failure",
                description="No ML predictions in the last 5 minutes",
                labels={"severity": "critical"}
            ),
            AlertRule(
                name="HighAnomalyRate",
                condition="anomaly_detection_rate > 0.5",
                severity="warning",
                duration="5m",
                summary="High anomaly detection rate",
                description="Anomaly detection rate is above 50%",
                labels={"severity": "warning"}
            )
        ]
    
    def _setup_notification_channels(self) -> Dict[str, Any]:
        """Setup notification channels."""
        return {
            'slack': {
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                'channel': os.getenv('SLACK_CHANNEL', '#alerts')
            },
            'email': {
                'smtp_server': os.getenv('SMTP_SERVER'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD'),
                'from_email': os.getenv('FROM_EMAIL'),
                'to_emails': os.getenv('TO_EMAILS', '').split(',')
            },
            'pagerduty': {
                'service_key': os.getenv('PAGERDUTY_SERVICE_KEY')
            }
        }
    
    def check_alerts(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check alert conditions and return active alerts."""
        active_alerts = []
        
        for rule in self.alert_rules:
            if self._evaluate_alert_condition(rule, metrics_data):
                alert = {
                    'name': rule.name,
                    'severity': rule.severity,
                    'summary': rule.summary,
                    'description': rule.description,
                    'labels': rule.labels,
                    'timestamp': datetime.utcnow().isoformat(),
                    'duration': rule.duration
                }
                
                active_alerts.append(alert)
                self._send_notification(alert)
        
        return active_alerts
    
    def _evaluate_alert_condition(self, rule: AlertRule, 
                                metrics_data: Dict[str, Any]) -> bool:
        """Evaluate alert condition based on metrics data."""
        # This is a simplified evaluation - in production, use Prometheus query API
        if rule.name == "HighErrorRate":
            error_rate = metrics_data.get('error_rate', 0)
            return error_rate > 0.1
        
        elif rule.name == "HighResponseTime":
            response_time = metrics_data.get('avg_response_time_ms', 0)
            return response_time > 1000
        
        elif rule.name == "HighCPUUsage":
            cpu_usage = metrics_data.get('cpu_usage_percent', 0)
            return cpu_usage > 80
        
        elif rule.name == "HighMemoryUsage":
            memory_usage_gb = metrics_data.get('memory_usage_gb', 0)
            return memory_usage_gb > 8
        
        elif rule.name == "DatabaseConnectionIssues":
            db_connections = metrics_data.get('database_connections', 0)
            return db_connections == 0
        
        elif rule.name == "MLPipelineFailure":
            ml_predictions = metrics_data.get('ml_predictions_per_minute', 0)
            return ml_predictions == 0
        
        elif rule.name == "HighAnomalyRate":
            anomaly_rate = metrics_data.get('anomaly_detection_rate', 0)
            return anomaly_rate > 0.5
        
        return False
    
    def _send_notification(self, alert: Dict[str, Any]):
        """Send alert notification through configured channels."""
        # Send to Slack
        if self.notification_channels['slack']['webhook_url']:
            self._send_slack_notification(alert)
        
        # Send email
        if self.notification_channels['email']['smtp_server']:
            self._send_email_notification(alert)
        
        # Send to PagerDuty
        if self.notification_channels['pagerduty']['service_key']:
            self._send_pagerduty_notification(alert)
    
    def _send_slack_notification(self, alert: Dict[str, Any]):
        """Send Slack notification."""
        try:
            webhook_url = self.notification_channels['slack']['webhook_url']
            channel = self.notification_channels['slack']['channel']
            
            message = {
                "channel": channel,
                "text": f"🚨 *{alert['severity'].upper()} Alert: {alert['name']}*",
                "attachments": [{
                    "color": "danger" if alert['severity'] == 'critical' else "warning",
                    "fields": [
                        {
                            "title": "Summary",
                            "value": alert['summary'],
                            "short": True
                        },
                        {
                            "title": "Description",
                            "value": alert['description'],
                            "short": False
                        },
                        {
                            "title": "Timestamp",
                            "value": alert['timestamp'],
                            "short": True
                        }
                    ]
                }]
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent for alert: {alert['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    def _send_email_notification(self, alert: Dict[str, Any]):
        """Send email notification."""
        # Implementation would use smtplib to send emails
        logger.info(f"Email notification would be sent for alert: {alert['name']}")
    
    def _send_pagerduty_notification(self, alert: Dict[str, Any]):
        """Send PagerDuty notification."""
        try:
            service_key = self.notification_channels['pagerduty']['service_key']
            
            payload = {
                "service_key": service_key,
                "event_type": "trigger",
                "description": alert['summary'],
                "client": "SmartCloudOps AI",
                "client_url": "https://smartcloudops.ai",
                "details": alert
            }
            
            response = requests.post(
                "https://events.pagerduty.com/generic/2010-04-15/create_event.json",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"PagerDuty notification sent for alert: {alert['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send PagerDuty notification: {e}")

class MonitoringDashboard:
    """Grafana dashboard configuration generator."""
    
    def __init__(self):
        self.dashboard_config = self._generate_dashboard_config()
    
    def _generate_dashboard_config(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration."""
        return {
            "dashboard": {
                "id": None,
                "title": "SmartCloudOps AI - Production Dashboard",
                "tags": ["smartcloudops", "production"],
                "timezone": "browser",
                "panels": [
                    # System Overview
                    {
                        "id": 1,
                        "title": "System Overview",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "cpu_usage_percent",
                                "legendFormat": "CPU Usage"
                            },
                            {
                                "expr": "memory_usage_bytes / 1024 / 1024 / 1024",
                                "legendFormat": "Memory Usage (GB)"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    # HTTP Requests
                    {
                        "id": 2,
                        "title": "HTTP Requests per Second",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{endpoint}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    # Response Time
                    {
                        "id": 3,
                        "title": "Response Time (95th percentile)",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                                "legendFormat": "{{method}} {{endpoint}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    # Error Rate
                    {
                        "id": 4,
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(errors_total[5m])",
                                "legendFormat": "{{type}} {{component}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    },
                    # ML Predictions
                    {
                        "id": 5,
                        "title": "ML Predictions per Second",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(ml_predictions_total[5m])",
                                "legendFormat": "{{model_version}} {{prediction_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    # Anomaly Detection Rate
                    {
                        "id": 6,
                        "title": "Anomaly Detection Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "anomaly_detection_rate",
                                "legendFormat": "{{model_version}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    },
                    # Database Connections
                    {
                        "id": 7,
                        "title": "Database Connections",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "database_connections_active",
                                "legendFormat": "Active Connections"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 24}
                    },
                    # Cache Hit Ratio
                    {
                        "id": 8,
                        "title": "Cache Hit Ratio",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "cache_hit_ratio",
                                "legendFormat": "Hit Ratio"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 24}
                    },
                    # Active Users
                    {
                        "id": 9,
                        "title": "Active Users",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "active_users",
                                "legendFormat": "Active Users"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 24}
                    },
                    # API Rate Limit Hits
                    {
                        "id": 10,
                        "title": "API Rate Limit Hits",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(api_rate_limit_hits[5m])",
                                "legendFormat": "{{endpoint}} {{user_id}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 24}
                    }
                ],
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "30s"
            }
        }
    
    def export_dashboard(self, filename: str = "grafana_dashboard.json"):
        """Export dashboard configuration to file."""
        with open(filename, 'w') as f:
            json.dump(self.dashboard_config, f, indent=2)
        
        logger.info(f"Dashboard configuration exported to: {filename}")

class ProductionMonitoring:
    """Main production monitoring system."""
    
    def __init__(self):
        self.metrics = ProductionMetrics()
        self.alert_manager = AlertManager()
        self.dashboard = MonitoringDashboard()
        self.flask_app = self._create_flask_app()
    
    def _create_flask_app(self) -> Flask:
        """Create Flask app for metrics endpoint."""
        app = Flask(__name__)
        
        @app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint."""
            return Response(
                generate_latest(self.metrics.registry),
                mimetype=CONTENT_TYPE_LATEST
            )
        
        @app.route('/health')
        def health():
            """Health check endpoint."""
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }
        
        @app.route('/alerts')
        def alerts():
            """Current alerts endpoint."""
            # This would query Prometheus for current alert state
            return {
                'alerts': self.alert_manager.alert_history,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return app
    
    def start_monitoring(self, host: str = '0.0.0.0', port: int = 9090):
        """Start the monitoring system."""
        logger.info(f"Starting production monitoring on {host}:{port}")
        
        # Export dashboard configuration
        self.dashboard.export_dashboard()
        
        # Start Flask app
        self.flask_app.run(host=host, port=port, debug=False)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_usage_percent': 0,  # Would be populated from actual metrics
                'memory_usage_gb': 0,
                'database_connections': 0,
                'redis_connections': 0
            },
            'application': {
                'http_requests_per_second': 0,
                'avg_response_time_ms': 0,
                'error_rate': 0,
                'active_users': 0
            },
            'ml_pipeline': {
                'predictions_per_minute': 0,
                'anomaly_detection_rate': 0,
                'avg_prediction_time_ms': 0
            },
            'alerts': {
                'active_alerts': 0,
                'critical_alerts': 0,
                'warning_alerts': 0
            }
        }

# Global monitoring instance
monitoring = ProductionMonitoring()

def get_monitoring() -> ProductionMonitoring:
    """Get the global monitoring instance."""
    return monitoring

if __name__ == "__main__":
    # Start monitoring system
    monitoring.start_monitoring()
