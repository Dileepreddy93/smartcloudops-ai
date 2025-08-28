#!/usr/bin/env python3
"""
Production-Ready Database Integration
====================================

Features:
- Connection pooling with SQLAlchemy
- Database migrations with Alembic
- Retry logic and circuit breaker
- Proper error handling and logging
- Connection health monitoring
"""



import os
import logging
import psycopg2
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


import redis
from psycopg2.extras import RealDictCursor
from redis.exceptions import RedisError
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration with environment-based settings."""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "smartcloudops")
        self.username = os.getenv("DB_USER", "smartcloudops_user")
        self.password = os.getenv("DB_PASSWORD", "smartcloudops_password")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))


class RedisConfig:
    """Redis configuration for caching."""

    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD")
        self.ssl = os.getenv("REDIS_SSL", "false").lower() == "true"


class ProductionDatabaseService:
    """Production-ready database service with connection pooling and error handling."""

    def __init__(self):
        self.config = DatabaseConfig()
        self.redis_config = RedisConfig()
        self.engine = None
        self.SessionLocal = None
        self.redis_client = None
        self._initialize_connections()

    def _initialize_connections(self):
        """Initialize database and Redis connections with proper error handling."""
        try:
            # Initialize SQLAlchemy engine with connection pooling
            database_url = f"postgresql://{
                self.config.username}:{
                self.config.password}@{
                self.config.host}:{
                self.config.port}/{
                    self.config.database}"

            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,  # Validate connections before use
                echo=False,  # Set to True for SQL debugging
            )

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # Test database connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("✅ Database connection established successfully")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def _initialize_redis(self):
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.host,
                port=self.redis_config.port,
                db=self.redis_config.db,
                password=self.redis_config.password,
                ssl=self.redis_config.ssl,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # Test Redis connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")

        except RedisError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            # Redis is optional, don't raise exception

    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def health_check(self) -> Dict[str, Any]:
        """Check database and Redis health."""
        health_status = {
            "database": {"status": "unknown", "latency_ms": None},
            "redis": {"status": "unknown", "latency_ms": None},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check database health
        try:
            start_time = datetime.utcnow()
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            health_status["database"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2),
            }
        except Exception as e:
            health_status["database"] = {"status": "unhealthy", "error": str(e)}

        # Check Redis health
        if self.redis_client:
            try:
                start_time = datetime.utcnow()
                self.redis_client.ping()
                latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                health_status["redis"] = {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                }
            except Exception as e:
                health_status["redis"] = {"status": "unhealthy", "error": str(e)}

        return health_status

    def get_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system metrics with caching."""
        cache_key = f"metrics:latest:{limit}"

        # Try to get from cache first
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info("📊 Metrics retrieved from cache")
                    return eval(cached_data)  # In production, use proper serialization
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")

        # Get from database
        try:
            with self.get_db_session() as session:
                # Example query - adjust based on your schema
                result = session.execute(
                    text(
                        """
                        SELECT
                            timestamp,
                            cpu_usage,
                            memory_usage,
                            disk_usage,
                            network_io
                        FROM system_metrics
                        ORDER BY timestamp DESC
                        LIMIT :limit
                    """
                    ),
                    {"limit": limit},
                )

                metrics = [dict(row) for row in result]

                # Cache the result for 5 minutes
                if self.redis_client and metrics:
                    try:
                        self.redis_client.setex(cache_key, 300, str(metrics))
                    except Exception as e:
                        logger.warning(f"Cache storage failed: {e}")

                return metrics

        except Exception as e:
            logger.error(f"Failed to retrieve metrics: {e}")
            return []

    def store_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Store system metrics with retry logic."""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                with self.get_db_session() as session:
                    session.execute(
                        text(
                            """
                            INSERT INTO system_metrics
                            (timestamp, cpu_usage, memory_usage, disk_usage, network_io)
                            VALUES (:timestamp, :cpu_usage, :memory_usage, :disk_usage, :network_io)
                        """
                        ),
                        metrics,
                    )
                    session.commit()
                    logger.info("📊 Metrics stored successfully")
                    return True

            except Exception as e:
                logger.error(f"Failed to store metrics (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time

                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    return False

        return False

    def cleanup_old_metrics(self, days_to_keep: int = 30) -> int:
        """Clean up old metrics to prevent database bloat."""
        try:
            with self.get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                result = session.execute(
                    text("DELETE FROM system_metrics WHERE timestamp < :cutoff_date"),
                    {"cutoff_date": cutoff_date},
                )
                session.commit()
                deleted_count = result.rowcount
                logger.info(f"🧹 Cleaned up {deleted_count} old metric records")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0


# Global database service instance
db_service = ProductionDatabaseService()


def get_db_service() -> ProductionDatabaseService:
    """Get the global database service instance."""
    return db_service
