#!/usr/bin/env python3
"""
Database Integration Module for SmartCloudOps AI
================================================

Provides database access layer for Flask application.
Integrates SQLite/PostgreSQL database with application logic.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add database path to imports
app_dir = Path(__file__).parent
database_dir = app_dir.parent / "database"
sys.path.insert(0, str(database_dir))

try:
    from sqlite_models import db_manager

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    db_manager = None

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service layer for Flask application."""

    def __init__(self):
        """Initialize database service."""
        self.db_manager = db_manager if DATABASE_AVAILABLE else None

        if not DATABASE_AVAILABLE:
            logger.warning("Database not available - using fallback mode")
        else:
            logger.info("✅ Database service initialized")

    def is_available(self) -> bool:
        """Check if database is available."""
        return DATABASE_AVAILABLE and self.db_manager is not None

    def get_metrics_count(self) -> int:
        """Get total number of metrics."""
        if not self.is_available():
            return 0

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM metrics")
                result = cursor.fetchone()
                return result["count"] if result else 0
        except Exception as e:
            logger.error(f"Error getting metrics count: {e}")
            return 0

    def get_latest_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest metrics from database."""
        if not self.is_available():
            return []

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT timestamp, source, cpu_usage, memory_usage, disk_usage,
                           response_time, is_anomaly, anomaly_score
                    FROM metrics 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            return []

    def get_anomalies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get anomalies from database."""
        if not self.is_available():
            return []

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT timestamp, source, cpu_usage, memory_usage, 
                           anomaly_score, response_time
                    FROM metrics 
                    WHERE is_anomaly = 1 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            return []

    def store_prediction(self, metrics: Dict[str, Any], prediction: Dict[str, Any]) -> bool:
        """Store prediction result in database."""
        if not self.is_available():
            logger.warning("Database not available - prediction not stored")
            return False

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Store prediction in anomaly_predictions table
                cursor.execute(
                    """
                    INSERT INTO anomaly_predictions (
                        timestamp, source, anomaly_detected, severity,
                        confidence_score, model_name, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now(timezone.utc).isoformat(),
                        metrics.get("source", "api_request"),
                        prediction.get("anomaly", False),
                        prediction.get("severity", "low"),
                        prediction.get("confidence", 0.0),
                        prediction.get("model_name", "real_data_anomaly_detector"),
                        prediction.get("model_version", "1.0.0"),
                    ),
                )

                conn.commit()
                logger.info("✅ Prediction stored in database")
                return True

        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            return False

    def store_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Store new metrics in database."""
        if not self.is_available():
            logger.warning("Database not available - metrics not stored")
            return False

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get system user ID
                cursor.execute("SELECT id FROM users WHERE username = 'system'")
                user_row = cursor.fetchone()
                system_user_id = user_row["id"] if user_row else None

                # Store metrics
                cursor.execute(
                    """
                    INSERT INTO metrics (
                        timestamp, source, cpu_usage, memory_usage, disk_usage,
                        load_1m, load_5m, load_15m, disk_io_read, disk_io_write,
                        network_rx, network_tx, response_time, error_rate,
                        is_anomaly, anomaly_score, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        metrics.get("source", "api"),
                        metrics.get("cpu_usage", 0.0),
                        metrics.get("memory_usage", 0.0),
                        metrics.get("disk_usage", 0.0),
                        metrics.get("load_1m", 0.0),
                        metrics.get("load_5m", 0.0),
                        metrics.get("load_15m", 0.0),
                        metrics.get("disk_io_read", 0),
                        metrics.get("disk_io_write", 0),
                        metrics.get("network_rx", 0),
                        metrics.get("network_tx", 0),
                        metrics.get("response_time", 0.0),
                        metrics.get("error_rate", 0.0),
                        metrics.get("is_anomaly", False),
                        metrics.get("anomaly_score", 0.0),
                        system_user_id,
                    ),
                )

                conn.commit()
                logger.info("✅ Metrics stored in database")
                return True

        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
            return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        if not self.is_available():
            return {"status": "database_unavailable"}

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get summary statistics
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_metrics,
                        AVG(cpu_usage) as avg_cpu,
                        MAX(cpu_usage) as max_cpu,
                        AVG(memory_usage) as avg_memory,
                        MAX(memory_usage) as max_memory,
                        AVG(response_time) as avg_response_time,
                        COUNT(CASE WHEN is_anomaly = 1 THEN 1 END) as total_anomalies
                    FROM metrics
                    WHERE timestamp >= datetime('now', '-24 hours')
                """
                )

                stats = cursor.fetchone()

                if stats:
                    return {
                        "status": "healthy",
                        "metrics_count": stats["total_metrics"],
                        "avg_cpu_usage": round(stats["avg_cpu"] or 0, 2),
                        "max_cpu_usage": round(stats["max_cpu"] or 0, 2),
                        "avg_memory_usage": round(stats["avg_memory"] or 0, 2),
                        "max_memory_usage": round(stats["max_memory"] or 0, 2),
                        "avg_response_time": round(stats["avg_response_time"] or 0, 2),
                        "anomalies_24h": stats["total_anomalies"],
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    return {"status": "no_data"}

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"status": "error", "message": str(e)}

    def get_model_info(self) -> Dict[str, Any]:
        """Get ML model information from database."""
        if not self.is_available():
            return {"status": "database_unavailable"}

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get deployed model information
                cursor.execute(
                    """
                    SELECT m.model_name, m.model_type, m.description,
                           mv.version, mv.accuracy, mv.precision_score,
                           mv.recall_score, mv.f1_score, mv.training_timestamp
                    FROM ml_models m
                    JOIN ml_model_versions mv ON m.id = mv.model_id
                    WHERE m.is_active = 1 AND mv.is_deployed = 1
                    ORDER BY mv.created_at DESC
                    LIMIT 1
                """
                )

                model = cursor.fetchone()

                if model:
                    return {
                        "model_name": model["model_name"],
                        "model_type": model["model_type"],
                        "version": model["version"],
                        "description": model["description"],
                        "performance": {
                            "accuracy": model["accuracy"],
                            "precision": model["precision_score"],
                            "recall": model["recall_score"],
                            "f1_score": model["f1_score"],
                        },
                        "training_timestamp": model["training_timestamp"],
                        "status": "deployed",
                    }
                else:
                    return {"status": "no_deployed_model"}

        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"status": "error", "message": str(e)}


# Global database service instance
db_service = DatabaseService()


def get_database_service() -> DatabaseService:
    """Get database service instance."""
    return db_service


def is_database_available() -> bool:
    """Check if database is available."""
    return db_service.is_available()


# Export functions for easy import
__all__ = [
    "DatabaseService",
    "db_service",
    "get_database_service",
    "is_database_available",
]
