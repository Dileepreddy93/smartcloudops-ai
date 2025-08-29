#!/usr/bin/env python3
"""
Database Integration Module for SmartCloudOps AI
================================================

Provides database access layer for Flask application using SQLAlchemy.
Integrates PostgreSQL/MySQL database with application logic.
"""


import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add database path to imports
app_dir = Path(__file__).parent
database_dir = app_dir.parent / "database"
sys.path.insert(0, str(database_dir))

try:
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    SQLAlchemy = None

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service layer for Flask application using SQLAlchemy."""

    def __init__(self, app=None, database_url: Optional[str] = None):
        """Initialize database service."""
        self.app = app
        self.db = None
        self.engine = None
        self.SessionLocal = None
        self.database_url = database_url
        
        if app:
            self.init_app(app)
        elif database_url:
            self._init_standalone(database_url)
        else:
            logger.warning("Database not configured - using fallback mode")

    def init_app(self, app):
        """Initialize database with Flask app."""
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available - using fallback mode")
            return

        try:
            # Configure SQLAlchemy
            app.config['SQLALCHEMY_DATABASE_URI'] = self.database_url or app.config.get('DATABASE_URL')
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True,
            }

            self.db = SQLAlchemy(app)
            self.engine = self.db.engine
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            with app.app_context():
                self.db.create_all()
            
            logger.info("✅ Database service initialized with Flask app")
            
        except Exception as e:
            logger.error(f"Failed to initialize database with Flask app: {e}")
            self.db = None

    def _init_standalone(self, database_url: str):
        """Initialize database service without Flask app."""
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available - using fallback mode")
            return

        try:
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info("✅ Database service initialized standalone")
            
        except Exception as e:
            logger.error(f"Failed to initialize standalone database: {e}")
            self.engine = None

    def get_session(self):
        """Get database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()

    def is_available(self) -> bool:
        """Check if database is available."""
        if not self.engine:
            return False
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_metrics_count(self) -> int:
        """Get total number of metrics."""
        if not self.is_available():
            return 0

        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT COUNT(*) as count FROM metrics"))
                row = result.fetchone()
                return row.count if row else 0
        except Exception as e:
            logger.error(f"Error getting metrics count: {e}")
            return 0

    def get_latest_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest metrics from database."""
        if not self.is_available():
            return []

        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT timestamp, source, cpu_usage, memory_usage, disk_usage,
                           response_time, is_anomaly, anomaly_score
                    FROM metrics 
                    ORDER BY timestamp DESC 
                    LIMIT :limit
                """), {"limit": limit})

                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            return []

    def get_anomalies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get anomalies from database."""
        if not self.is_available():
            return []

        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT timestamp, source, cpu_usage, memory_usage, 
                           anomaly_score, response_time
                    FROM metrics 
                    WHERE is_anomaly = 1 
                    ORDER BY timestamp DESC 
                    LIMIT :limit
                """), {"limit": limit})

                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            return []

    def store_prediction(self, metrics: Dict[str, Any], prediction: Dict[str, Any]) -> bool:
        """Store prediction result in database."""
        if not self.is_available():
            logger.warning("Database not available - prediction not stored")
            return False

        try:
            with self.get_session() as session:
                # Store prediction in anomaly_predictions table
                session.execute(text("""
                    INSERT INTO anomaly_predictions (
                        timestamp, source, anomaly_detected, severity,
                        confidence_score, model_name, model_version
                    ) VALUES (:timestamp, :source, :anomaly_detected, :severity, 
                             :confidence_score, :model_name, :model_version)
                """), {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": metrics.get("source", "api_request"),
                    "anomaly_detected": prediction.get("anomaly", False),
                    "severity": prediction.get("severity", "low"),
                    "confidence_score": prediction.get("confidence", 0.0),
                    "model_name": prediction.get("model_name", "real_data_anomaly_detector"),
                    "model_version": prediction.get("model_version", "1.0.0"),
                })

                session.commit()
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
            with self.get_session() as session:
                # Get system user ID
                result = session.execute(text("SELECT id FROM users WHERE username = 'system'"))
                user_row = result.fetchone()
                system_user_id = user_row.id if user_row else None

                # Store metrics
                session.execute(text("""
                    INSERT INTO metrics (
                        timestamp, source, cpu_usage, memory_usage, disk_usage,
                        load_1m, load_5m, load_15m, disk_io_read, disk_io_write,
                        network_rx, network_tx, response_time, error_rate,
                        is_anomaly, anomaly_score, created_by
                    ) VALUES (:timestamp, :source, :cpu_usage, :memory_usage, :disk_usage,
                             :load_1m, :load_5m, :load_15m, :disk_io_read, :disk_io_write,
                             :network_rx, :network_tx, :response_time, :error_rate,
                             :is_anomaly, :anomaly_score, :created_by)
                """), {
                    "timestamp": metrics.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "source": metrics.get("source", "api"),
                    "cpu_usage": metrics.get("cpu_usage", 0.0),
                    "memory_usage": metrics.get("memory_usage", 0.0),
                    "disk_usage": metrics.get("disk_usage", 0.0),
                    "load_1m": metrics.get("load_1m", 0.0),
                    "load_5m": metrics.get("load_5m", 0.0),
                    "load_15m": metrics.get("load_15m", 0.0),
                    "disk_io_read": metrics.get("disk_io_read", 0),
                    "disk_io_write": metrics.get("disk_io_write", 0),
                    "network_rx": metrics.get("network_rx", 0),
                    "network_tx": metrics.get("network_tx", 0),
                    "response_time": metrics.get("response_time", 0.0),
                    "error_rate": metrics.get("error_rate", 0.0),
                    "is_anomaly": metrics.get("is_anomaly", False),
                    "anomaly_score": metrics.get("anomaly_score", 0.0),
                    "created_by": system_user_id,
                })

                session.commit()
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
            with self.get_session() as session:
                result = session.execute(text("""
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
                """))

                stats = result.fetchone()

                if stats:
                    return {
                        "status": "healthy",
                        "metrics_count": stats.total_metrics,
                        "avg_cpu_usage": round(stats.avg_cpu or 0, 2),
                        "max_cpu_usage": round(stats.max_cpu or 0, 2),
                        "avg_memory_usage": round(stats.avg_memory or 0, 2),
                        "max_memory_usage": round(stats.max_memory or 0, 2),
                        "avg_response_time": round(stats.avg_response_time or 0, 2),
                        "anomalies_24h": stats.total_anomalies,
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
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT m.model_name, m.model_type, m.description,
                           mv.version, mv.accuracy, mv.precision_score,
                           mv.recall_score, mv.f1_score, mv.training_timestamp
                    FROM ml_models m
                    JOIN ml_model_versions mv ON m.id = mv.model_id
                    WHERE m.is_active = 1 AND mv.is_deployed = 1
                    ORDER BY mv.created_at DESC
                    LIMIT 1
                """))

                model = result.fetchone()

                if model:
                    return {
                        "model_name": model.model_name,
                        "model_type": model.model_type,
                        "version": model.version,
                        "description": model.description,
                        "performance": {
                            "accuracy": model.accuracy,
                            "precision": model.precision_score,
                            "recall": model.recall_score,
                            "f1_score": model.f1_score,
                        },
                        "training_timestamp": model.training_timestamp,
                        "status": "deployed",
                    }
                else:
                    return {"status": "no_deployed_model"}

        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"status": "error", "message": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            if not self.is_available():
                return {
                    "status": "unhealthy",
                    "error": "Database connection failed",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            # Test basic operations
            with self.get_session() as session:
                # Test read
                result = session.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()
                
                if not test_result or test_result.test != 1:
                    raise Exception("Database read test failed")

                # Test write (if possible)
                try:
                    session.execute(text("SELECT COUNT(*) FROM metrics"))
                    session.commit()
                except Exception:
                    # Table might not exist, that's okay for health check
                    pass

            return {
                "status": "healthy",
                "database_type": self.engine.url.drivername if self.engine else "unknown",
                "connection_pool_size": self.engine.pool.size() if self.engine else 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


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
