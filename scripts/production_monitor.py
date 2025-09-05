#!/usr/bin/env python3
"""
SmartCloudOps AI - Production Monitoring & Alerting System
=========================================================

Implements comprehensive monitoring with proactive alerting.
Critical for production operations with 10-50 users.
"""


import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

import psutil
import requests


class ProductionMonitor:
    """Production-grade monitoring and alerting system"""

    def __init__(self):
        self.app_url = os.getenv("APP_URL", "http://localhost:5000")
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.alert_email = os.getenv("ALERT_EMAIL", "admin@smartcloudops.ai")
        self.smtp_config = {
            "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
        }
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time_ms": 5000,
            "error_rate_percent": 5.0,
            "ml_accuracy": 0.75,
        }
        self.alert_cooldown = {}  # Prevent spam
        self.setup_logging()

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler("/var/log/smartcloudops/monitoring.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def check_system_health(self) -> Dict[str, Any]:
        """Check system resource health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"System health check failed: {e}")
            return {}

    def check_application_health(self) -> Dict[str, Any]:
        """Check application health and performance"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.app_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000

            health_data = {
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "is_healthy": response.status_code == 200,
                "timestamp": datetime.now().isoformat(),
            }

            if response.status_code == 200:
                try:
                    app_data = response.json()
                    health_data.update(app_data)
                except Exception:
                    pass

            return health_data

        except Exception as e:
            self.logger.error(f"Application health check failed: {e}")
            return {
                "status_code": 0,
                "response_time_ms": 0,
                "is_healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def check_ml_performance(self) -> Dict[str, Any]:
        """Check ML model performance"""
        try:
            response = requests.get(f"{self.app_url}/ml/metrics", timeout=10)

            if response.status_code == 200:
                ml_data = response.json()
                return {
                    "ml_available": True,
                    "accuracy": ml_data.get("metrics", {}).get("accuracy", 0),
                    "predictions_count": ml_data.get("metrics", {}).get("total_predictions", 0),
                    "avg_response_time": ml_data.get("metrics", {}).get("avg_prediction_time", 0),
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "ml_available": False,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"ML performance check failed: {e}")
            return {
                "ml_available": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Test database through application endpoint
            response = requests.get(f"{self.app_url}/metrics", timeout=10)

            if response.status_code == 200:
                return {
                    "db_available": True,
                    "response_time_ms": 0,  # Could measure this
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "db_available": False,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "db_available": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def send_alert(self, subject: str, message: str, severity: str = "WARNING"):
        """Send email alert"""
        try:
            # Check cooldown
            alert_key = f"{subject}_{severity}"
            now = datetime.now()

            if alert_key in self.alert_cooldown:
                if now - self.alert_cooldown[alert_key] < timedelta(minutes=15):
                    return  # Skip alert due to cooldown

            self.alert_cooldown[alert_key] = now

            # Create email
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config["username"]
            msg["To"] = self.alert_email
            msg["Subject"] = f"🚨 SmartCloudOps AI - {severity}: {subject}"

            body = f"""
SmartCloudOps AI Production Alert

Severity: {severity}
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
Subject: {subject}

Details:
{message}

System Information:
- Application URL: {self.app_url}
- Prometheus URL: {self.prometheus_url}

This is an automated alert from the SmartCloudOps AI monitoring system.
"""

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(self.smtp_config["server"], self.smtp_config["port"])
            server.starttls()
            server.login(self.smtp_config["username"], self.smtp_config["password"])
            text = msg.as_string()
            server.sendmail(self.smtp_config["username"], self.alert_email, text)
            server.quit()

            self.logger.info(f"Alert sent: {subject}")

        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")

    def analyze_and_alert(self, system_health: Dict, app_health: Dict, ml_health: Dict, db_health: Dict):
        """Analyze metrics and send alerts if needed"""

        # System resource alerts
        if system_health.get("cpu_percent", 0) > self.thresholds["cpu_percent"]:
            self.send_alert(
                "High CPU Usage",
                f"CPU usage is {system_health['cpu_percent']:.1f}% (threshold: {self.thresholds['cpu_percent']}%)",
                "CRITICAL",
            )

        if system_health.get("memory_percent", 0) > self.thresholds["memory_percent"]:
            self.send_alert(
                "High Memory Usage",
                (
                    f"Memory usage is {system_health['memory_percent']:.1f}% "
                    f"(threshold: {self.thresholds['memory_percent']}%)"
                ),
                "CRITICAL",
            )

        if system_health.get("disk_percent", 0) > self.thresholds["disk_percent"]:
            self.send_alert(
                "High Disk Usage",
                f"Disk usage is {system_health['disk_percent']:.1f}% (threshold: {self.thresholds['disk_percent']}%)",
                "CRITICAL",
            )

        # Application health alerts
        if not app_health.get("is_healthy", False):
            self.send_alert(
                "Application Down",
                f"Application health check failed: {app_health.get('error', 'Unknown error')}",
                "CRITICAL",
            )

        if app_health.get("response_time_ms", 0) > self.thresholds["response_time_ms"]:
            self.send_alert(
                "Slow Response Time",
                (
                    f"Response time is {app_health['response_time_ms']:.0f}ms "
                    f"(threshold: {self.thresholds['response_time_ms']}ms)"
                ),
                "WARNING",
            )

        # ML performance alerts
        if ml_health.get("accuracy", 1.0) < self.thresholds["ml_accuracy"]:
            self.send_alert(
                "ML Model Performance Degraded",
                f"ML accuracy is {ml_health['accuracy']:.3f} (threshold: {self.thresholds['ml_accuracy']})",
                "WARNING",
            )

        if not ml_health.get("ml_available", True):
            self.send_alert(
                "ML Service Unavailable",
                f"ML service check failed: {ml_health.get('error', 'Unknown error')}",
                "CRITICAL",
            )

        # Database alerts
        if not db_health.get("db_available", True):
            self.send_alert(
                "Database Unavailable",
                f"Database connectivity failed: {db_health.get('error', 'Unknown error')}",
                "CRITICAL",
            )

    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        self.logger.info("Starting monitoring cycle...")

        # Collect metrics
        system_health = self.check_system_health()
        app_health = self.check_application_health()
        ml_health = self.check_ml_performance()
        db_health = self.check_database_health()

        # Log current status
        self.logger.info(
            f"System: CPU {system_health.get('cpu_percent', 0):.1f}%, "
            f"Memory {system_health.get('memory_percent', 0):.1f}%, "
            f"Disk {system_health.get('disk_percent', 0):.1f}%"
        )

        self.logger.info(
            f"Application: Status {app_health.get('status_code', 0)}, "
            f"Response {app_health.get('response_time_ms', 0):.0f}ms"
        )

        # Analyze and send alerts
        self.analyze_and_alert(system_health, app_health, ml_health, db_health)

        # Store metrics (could save to database or Prometheus)
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": system_health,
            "application": app_health,
            "ml": ml_health,
            "database": db_health,
        }

        # Save to monitoring log
        with open("/var/log/smartcloudops/metrics.jsonl", "a") as f:
            f.write(json.dumps(metrics) + "\n")

        self.logger.info("Monitoring cycle completed")

    def run_continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous monitoring"""
        self.logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring cycle failed: {e}")
                time.sleep(interval_seconds)


def create_monitoring_service():
    """Create systemd service for monitoring"""
    service_content = """[Unit]
Description=SmartCloudOps AI Production Monitoring
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/smartcloudops-ai/scripts
ExecStart=/home/ec2-user/smartcloudops-ai/venv/bin/python3 production_monitor.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/home/ec2-user/smartcloudops-ai

[Install]
WantedBy=multi-user.target
"""

    with open("/tmp/smartcloudops-monitoring.service", "w") as f:
        f.write(service_content)

    print("✅ Monitoring service file created at /tmp/smartcloudops-monitoring.service")
    print("To install: sudo mv /tmp/smartcloudops-monitoring.service /etc/systemd/system/")
    print("Then: sudo systemctl enable smartcloudops-monitoring && sudo systemctl start smartcloudops-monitoring")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "create-service":
        create_monitoring_service()
    else:
        monitor = ProductionMonitor()
        monitor.run_continuous_monitoring()
