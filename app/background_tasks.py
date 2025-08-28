#!/usr/bin/env python3
"""
SmartCloudOps AI - Background Task Processing
=============================================

Asynchronous task processing system using Celery for ML training,
data processing, and system maintenance tasks.
"""

import logging
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.cache_service import cache_service
from app.core.ml_engine.secure_inference import SecureMLInferenceEngine
from app.utils.response import build_error_response, build_success_response

try:
    from celery import Celery, Task
    from celery.utils.log import get_task_logger

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None
    Task = None

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


logger = logging.getLogger(__name__)

# Initialize Celery app
if CELERY_AVAILABLE:
    celery_app = Celery("smartcloudops")

    # Configure Celery
    celery_app.conf.update(
        broker_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        result_backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_routes={
            "app.background_tasks.train_ml_model": {"queue": "ml_training"},
            "app.background_tasks.process_metrics_data": {"queue": "data_processing"},
            "app.background_tasks.system_maintenance": {"queue": "maintenance"},
            "app.background_tasks.send_notifications": {"queue": "notifications"},
        },
        task_default_queue="default",
        task_default_exchange="smartcloudops",
        task_default_routing_key="smartcloudops.default",
    )
else:
    celery_app = None


class SmartCloudOpsTask(Task):
    """Base task class with error handling and logging."""

    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion."""
        logger.info(f"Task {task_id} completed successfully")
        cache_service.set(
            f"task_status:{task_id}",
            {
                "status": "completed",
                "result": retval,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
            ttl=3600,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        error_details = {
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "args": args,
            "kwargs": kwargs,
        }
        logger.error(f"Task {task_id} failed: {error_details}")
        cache_service.set(
            f"task_status:{task_id}",
            {
                "status": "failed",
                "error": error_details,
                "failed_at": datetime.now(timezone.utc).isoformat(),
            },
            ttl=3600,
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Task {task_id} retrying: {exc}")
        cache_service.set(
            f"task_status:{task_id}",
            {
                "status": "retrying",
                "retry_count": self.request.retries,
                "error": str(exc),
                "retried_at": datetime.now(timezone.utc).isoformat(),
            },
            ttl=3600,
        )


@celery_app.task(base=SmartCloudOpsTask, bind=True, max_retries=3)
def train_ml_model(
    self,
    model_type: str = "anomaly_detection",
    training_data_path: Optional[str] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Train ML model in background.

    Args:
        model_type: Type of model to train
        training_data_path: Path to training data
        hyperparameters: Model hyperparameters

    Returns:
        Training results
    """
    try:
        logger.info(f"Starting ML model training: {model_type}")

        # Initialize ML engine
        ml_engine = SecureMLInferenceEngine()

        # Set training parameters
        if hyperparameters:
            ml_engine.set_hyperparameters(hyperparameters)

        # Train model
        training_result = ml_engine._train_model(model_type=model_type, data_path=training_data_path)

        # Cache training results
        cache_service.set(
            f"ml_training:{model_type}:{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            training_result,
            ttl=86400,
        )

        logger.info(f"ML model training completed: {model_type}")
        return build_success_response(data=training_result, message=f"ML model {model_type} trained successfully")

    except Exception as exc:
        logger.error(f"ML model training failed: {exc}")
        raise self.retry(countdown=60, exc=exc)


@celery_app.task(base=SmartCloudOpsTask, bind=True, max_retries=3)
def process_metrics_data(self, metrics_data: List[Dict[str, Any]], operation: str = "analyze") -> Dict[str, Any]:
    """
    Process metrics data in background.

    Args:
        metrics_data: List of metrics to process
        operation: Processing operation (analyze, aggregate, clean)

    Returns:
        Processing results
    """
    try:
        logger.info(f"Starting metrics data processing: {operation}")

        results = {
            "processed_count": 0,
            "anomalies_detected": 0,
            "aggregated_metrics": {},
            "processing_time": 0,
        }

        start_time = time.time()

        # Initialize ML engine for anomaly detection
        ml_engine = SecureMLInferenceEngine()

        for metric in metrics_data:
            try:
                # Validate metric data
                if not all(key in metric for key in ["cpu_usage", "memory_usage", "timestamp"]):
                    continue

                # Detect anomalies
                prediction = ml_engine.predict(metric)
                if prediction.get("is_anomaly", False):
                    results["anomalies_detected"] += 1

                results["processed_count"] += 1

            except Exception as e:
                logger.warning(f"Failed to process metric: {e}")
                continue

        results["processing_time"] = time.time() - start_time

        # Cache results
        cache_service.set(
            f"metrics_processing:{operation}:{datetime.now(timezone.utc).strftime('%Y%m%d_%H')}",
            results,
            ttl=3600,
        )

        logger.info(f"Metrics processing completed: {results['processed_count']} processed")
        return build_success_response(data=results, message=f"Processed {results['processed_count']} metrics")

    except Exception as exc:
        logger.error(f"Metrics processing failed: {exc}")
        raise self.retry(countdown=30, exc=exc)


@celery_app.task(base=SmartCloudOpsTask, bind=True, max_retries=2)
def system_maintenance(self, maintenance_type: str = "cleanup") -> Dict[str, Any]:
    """
    Perform system maintenance tasks.

    Args:
        maintenance_type: Type of maintenance (cleanup, backup, health_check)

    Returns:
        Maintenance results
    """
    try:
        logger.info(f"Starting system maintenance: {maintenance_type}")

        results = {
            "maintenance_type": maintenance_type,
            "completed_tasks": [],
            "errors": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        if maintenance_type == "cleanup":
            # Clean up old cache entries
            deleted_count = cache_service.clear("smartcloudops:old:*")
            results["completed_tasks"].append(f"Cleaned {deleted_count} old cache entries")

            # Clean up old logs
            log_cleanup_result = cleanup_old_logs()
            results["completed_tasks"].append(log_cleanup_result)

        elif maintenance_type == "backup":
            # Backup ML models
            backup_result = backup_ml_models()
            results["completed_tasks"].append(backup_result)

            # Backup configuration
            config_backup_result = backup_configuration()
            results["completed_tasks"].append(config_backup_result)

        elif maintenance_type == "health_check":
            # Perform comprehensive health check
            health_result = perform_system_health_check()
            results["completed_tasks"].append(health_result)

        results["completed_at"] = datetime.now(timezone.utc).isoformat()

        # Cache maintenance results
        cache_service.set(
            f"maintenance:{maintenance_type}:{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            results,
            ttl=86400,
        )

        logger.info(f"System maintenance completed: {maintenance_type}")
        return build_success_response(data=results, message=f"System maintenance {maintenance_type} completed")

    except Exception as exc:
        logger.error(f"System maintenance failed: {exc}")
        raise self.retry(countdown=300, exc=exc)


@celery_app.task(base=SmartCloudOpsTask, bind=True, max_retries=3)
def send_notifications(
    self,
    notification_type: str,
    recipients: List[str],
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send notifications in background.

    Args:
        notification_type: Type of notification (email, slack, webhook)
        recipients: List of recipients
        message: Notification message
        data: Additional data for notification

    Returns:
        Notification results
    """
    try:
        logger.info(f"Sending {notification_type} notification to {len(recipients)} recipients")

        results = {
            "notification_type": notification_type,
            "recipients": recipients,
            "sent_count": 0,
            "failed_count": 0,
            "errors": [],
        }

        if notification_type == "email":
            for recipient in recipients:
                try:
                    send_email_notification(recipient, message, data)
                    results["sent_count"] += 1
                except Exception as e:
                    results["failed_count"] += 1
                    results["errors"].append(f"Failed to send email to {recipient}: {e}")

        elif notification_type == "slack":
            try:
                send_slack_notification(recipients, message, data)
                results["sent_count"] = len(recipients)
            except Exception as e:
                results["failed_count"] = len(recipients)
                results["errors"].append(f"Failed to send Slack notification: {e}")

        elif notification_type == "webhook":
            for webhook_url in recipients:
                try:
                    send_webhook_notification(webhook_url, message, data)
                    results["sent_count"] += 1
                except Exception as e:
                    results["failed_count"] += 1
                    results["errors"].append(f"Failed to send webhook to {webhook_url}: {e}")

        # Cache notification results
        cache_service.set(
            f"notification:{notification_type}:{datetime.now(timezone.utc).strftime('%Y%m%d_%H')}",
            results,
            ttl=3600,
        )

        logger.info(f"Notification sent: {results['sent_count']} successful, {results['failed_count']} failed")
        return build_success_response(data=results, message=f"Sent {results['sent_count']} notifications")

    except Exception as exc:
        logger.error(f"Notification sending failed: {exc}")
        raise self.retry(countdown=60, exc=exc)


@celery_app.task(base=SmartCloudOpsTask, bind=True, max_retries=2)
def update_system_metrics(self) -> Dict[str, Any]:
    """
    Update system metrics in background.

    Returns:
        Metrics update results
    """
    try:
        logger.info("Updating system metrics")

        # Collect system metrics
        metrics = collect_system_metrics()

        # Store metrics
        cache_service.set("system_metrics:current", metrics, ttl=300)

        # Check for anomalies
        ml_engine = SecureMLInferenceEngine()
        anomaly_result = ml_engine.predict(metrics)

        if anomaly_result.get("is_anomaly", False):
            # Trigger alert
            send_notifications.delay(
                notification_type="slack",
                recipients=[os.getenv("ALERT_WEBHOOK_URL", "")],
                message=f"System anomaly detected: {anomaly_result.get('confidence', 0):.2f} confidence",
                data=anomaly_result,
            )

        logger.info("System metrics updated successfully")
        return build_success_response(
            data={
                "metrics_updated": True,
                "anomaly_detected": anomaly_result.get("is_anomaly", False),
            },
            message="System metrics updated",
        )

    except Exception as exc:
        logger.error(f"System metrics update failed: {exc}")
        raise self.retry(countdown=30, exc=exc)


# Helper functions
def cleanup_old_logs() -> str:
    """Clean up old log files."""
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            return "No logs directory found"

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        deleted_count = 0

        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                deleted_count += 1

        return f"Cleaned {deleted_count} old log files"
    except Exception as e:
        return f"Log cleanup failed: {e}"


def backup_ml_models() -> str:
    """Backup ML models."""
    try:
        ml_models_dir = Path("ml_models")
        if not ml_models_dir.exists():
            return "No ML models directory found"

        # Create backup directory
        backup_dir = Path("backups") / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy models
        import shutil

        shutil.copytree(ml_models_dir, backup_dir / "ml_models")

        return f"ML models backed up to {backup_dir}"
    except Exception as e:
        return f"ML model backup failed: {e}"


def backup_configuration() -> str:
    """Backup configuration files."""
    try:
        config_files = [".env", "config.py", "requirements.txt"]
        backup_dir = Path("backups") / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        copied_count = 0
        for config_file in config_files:
            if Path(config_file).exists():
                import shutil

                shutil.copy2(config_file, backup_dir)
                copied_count += 1

        return f"Configuration backed up: {copied_count} files"
    except Exception as e:
        return f"Configuration backup failed: {e}"


def perform_system_health_check() -> str:
    """Perform comprehensive system health check."""
    try:
        health_status = {
            "database": check_database_health(),
            "cache": check_cache_health(),
            "ml_service": check_ml_service_health(),
            "disk_space": check_disk_space(),
            "memory_usage": check_memory_usage(),
        }

        overall_health = all(health_status.values())

        # Cache health status
        cache_service.set("system_health", health_status, ttl=300)

        return f"Health check completed: {'healthy' if overall_health else 'unhealthy'}"
    except Exception as e:
        return f"Health check failed: {e}"


def collect_system_metrics() -> Dict[str, Any]:
    """Collect current system metrics."""
    try:
        import psutil

        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "load_1m": psutil.getloadavg()[0],
            "load_5m": psutil.getloadavg()[1],
            "load_15m": psutil.getloadavg()[2],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")
        return {}


def check_database_health() -> bool:
    """Check database health."""
    try:
        # Add your database health check logic here
        return True
    except Exception:
        return False


def check_cache_health() -> bool:
    """Check cache health."""
    try:
        health = cache_service.health_check()
        return health.get("status") == "healthy"
    except Exception:
        return False


def check_ml_service_health() -> bool:
    """Check ML service health."""
    try:
        ml_engine = SecureMLInferenceEngine()
        health = ml_engine.health_check()
        return health.get("status") == "healthy"
    except Exception:
        return False


def check_disk_space() -> bool:
    """Check disk space."""
    try:
        import psutil

        usage = psutil.disk_usage("/")
        return usage.percent < 90
    except Exception:
        return False


def check_memory_usage() -> bool:
    """Check memory usage."""
    try:
        import psutil

        memory = psutil.virtual_memory()
        return memory.percent < 90
    except Exception:
        return False


def send_email_notification(recipient: str, message: str, data: Optional[Dict[str, Any]] = None):
    """Send email notification."""
    # Implement email sending logic
    logger.info(f"Email notification sent to {recipient}")


def send_slack_notification(webhook_urls: List[str], message: str, data: Optional[Dict[str, Any]] = None):
    """Send Slack notification."""
    # Implement Slack webhook sending logic
    logger.info(f"Slack notification sent to {len(webhook_urls)} webhooks")


def send_webhook_notification(webhook_url: str, message: str, data: Optional[Dict[str, Any]] = None):
    """Send webhook notification."""
    # Implement webhook sending logic
    logger.info(f"Webhook notification sent to {webhook_url}")


# Task scheduling
def schedule_periodic_tasks():
    """Schedule periodic background tasks."""
    if not CELERY_AVAILABLE:
        logger.warning("Celery not available, skipping task scheduling")
        return

    # Schedule system metrics update every 5 minutes
    update_system_metrics.apply_async(countdown=300)

    # Schedule system maintenance daily at 2 AM
    system_maintenance.apply_async(
        kwargs={"maintenance_type": "cleanup"},
        eta=datetime.now(timezone.utc).replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1),
    )


# Task status utilities
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get task status by ID."""
    if not CELERY_AVAILABLE:
        return {"status": "celery_not_available"}

    # Check cache first
    cached_status = cache_service.get(f"task_status:{task_id}")
    if cached_status:
        return cached_status

    # Check Celery result
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "status": result.status,
            "result": result.result if result.ready() else None,
            "task_id": task_id,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def cancel_task(task_id: str) -> bool:
    """Cancel a running task."""
    if not CELERY_AVAILABLE:
        return False

    try:
        celery_app.control.revoke(task_id, terminate=True)
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return False


# Initialize periodic tasks
if __name__ == "__main__":
    schedule_periodic_tasks()
