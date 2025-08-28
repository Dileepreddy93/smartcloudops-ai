#!/usr/bin/env python3
"""
SmartCloudOps AI - Database Connection Pooling
=============================================

Database connection pooling system for improved performance and resource management.
"""

import atexit
import logging
import os
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.cache_service import cache_service
from app.utils.response import build_error_response, build_success_response

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    pool = None

try:
    import mysql.connector
    from mysql.connector import pooling

    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    mysql = None

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


logger = logging.getLogger(__name__)


class DatabasePool:
    """Database connection pool manager."""

    def __init__(self, db_type: str = "postgresql", **kwargs):
        """
        Initialize database pool.

        Args:
            db_type: Database type ('postgresql' or 'mysql')
            **kwargs: Database connection parameters
        """
        self.db_type = db_type.lower()
        self.pool = None
        self.pool_config = kwargs
        self.stats = {
            "connections_created": 0,
            "connections_used": 0,
            "connections_returned": 0,
            "connection_errors": 0,
            "pool_errors": 0,
        }
        self.lock = threading.Lock()

        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            if self.db_type == "postgresql" and POSTGRES_AVAILABLE:
                self._init_postgresql_pool()
            elif self.db_type == "mysql" and MYSQL_AVAILABLE:
                self._init_mysql_pool()
            else:
                logger.error(f"Database type {self.db_type} not supported or not available")
                raise ValueError(f"Unsupported database type: {self.db_type}")

            logger.info(f"Database pool initialized for {self.db_type}")

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    def _init_postgresql_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            # Extract PostgreSQL connection parameters
            host = self.pool_config.get("host", "localhost")
            port = self.pool_config.get("port", 5432)
            database = self.pool_config.get("database", "smartcloudops")
            user = self.pool_config.get("user", "postgres")
            password = self.pool_config.get("password", "")

            # Pool configuration
            min_connections = self.pool_config.get("min_connections", 5)
            max_connections = self.pool_config.get("max_connections", 20)

            # Create connection pool
            self.pool = pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                cursor_factory=RealDictCursor,
                connect_timeout=10,
                application_name="SmartCloudOps",
            )

            logger.info(f"PostgreSQL pool created: {min_connections}-{max_connections} connections")

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL pool: {e}")
            raise

    def _init_mysql_pool(self):
        """Initialize MySQL connection pool."""
        try:
            # Extract MySQL connection parameters
            host = self.pool_config.get("host", "localhost")
            port = self.pool_config.get("port", 3306)
            database = self.pool_config.get("database", "smartcloudops")
            user = self.pool_config.get("user", "root")
            password = self.pool_config.get("password", "")

            # Pool configuration
            pool_size = self.pool_config.get("pool_size", 10)
            pool_reset_session = self.pool_config.get("pool_reset_session", True)

            # Create connection pool
            self.pool = pooling.MySQLConnectionPool(
                pool_name="smartcloudops_pool",
                pool_size=pool_size,
                pool_reset_session=pool_reset_session,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                autocommit=True,
                charset="utf8mb4",
            )

            logger.info(f"MySQL pool created: {pool_size} connections")

        except Exception as e:
            logger.error(f"Failed to create MySQL pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Get a database connection from the pool.

        Yields:
            Database connection object
        """
        connection = None
        try:
            with self.lock:
                self.stats["connections_used"] += 1

            if self.db_type == "postgresql":
                connection = self.pool.getconn()
                if connection:
                    self.stats["connections_created"] += 1
                else:
                    self.stats["pool_errors"] += 1
                    raise Exception("Failed to get connection from pool")

            elif self.db_type == "mysql":
                connection = self.pool.get_connection()
                if connection:
                    self.stats["connections_created"] += 1
                else:
                    self.stats["pool_errors"] += 1
                    raise Exception("Failed to get connection from pool")

            yield connection

        except Exception as e:
            self.stats["connection_errors"] += 1
            logger.error(f"Database connection error: {e}")
            raise

        finally:
            if connection:
                try:
                    if self.db_type == "postgresql":
                        self.pool.putconn(connection)
                    elif self.db_type == "mysql":
                        connection.close()

                    with self.lock:
                        self.stats["connections_returned"] += 1

                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    connection.commit()
                    return [{"affected_rows": cursor.rowcount}]

            except Exception as e:
                connection.rollback()
                logger.error(f"Query execution error: {e}")
                raise
            finally:
                cursor.close()

    def execute_many(self, query: str, params_list: List[tuple]) -> Dict[str, Any]:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples

        Returns:
            Execution results
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.executemany(query, params_list)
                connection.commit()
                return {"affected_rows": cursor.rowcount}

            except Exception as e:
                connection.rollback()
                logger.error(f"Batch execution error: {e}")
                raise
            finally:
                cursor.close()

    def execute_transaction(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple queries in a transaction.

        Args:
            queries: List of query dictionaries with 'query' and 'params' keys

        Returns:
            Transaction results
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                results = []
                for query_dict in queries:
                    query = query_dict["query"]
                    params = query_dict.get("params")

                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if query.strip().upper().startswith("SELECT"):
                        results.append(cursor.fetchall())
                    else:
                        results.append({"affected_rows": cursor.rowcount})

                connection.commit()
                return {"results": results, "success": True}

            except Exception as e:
                connection.rollback()
                logger.error(f"Transaction error: {e}")
                return {"error": str(e), "success": False}
            finally:
                cursor.close()

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the database pool.

        Returns:
            Health check results
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()

                # Test basic connectivity
                if self.db_type == "postgresql":
                    cursor.execute("SELECT 1 as test")
                elif self.db_type == "mysql":
                    cursor.execute("SELECT 1 as test")

                result = cursor.fetchone()
                cursor.close()

                if result and result[0] == 1:
                    return {
                        "status": "healthy",
                        "database_type": self.db_type,
                        "pool_stats": self.get_stats(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Health check query failed",
                        "database_type": self.db_type,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_type": self.db_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Pool statistics
        """
        with self.lock:
            stats_copy = self.stats.copy()

        # Add pool-specific stats
        if self.db_type == "postgresql" and self.pool:
            try:
                stats_copy["pool_size"] = self.pool.get_size()
                stats_copy["available_connections"] = self.pool.get_size() - self.pool.get_used()
            except Exception:
                stats_copy["pool_size"] = "unknown"
                stats_copy["available_connections"] = "unknown"

        return stats_copy

    def reset_stats(self):
        """Reset pool statistics."""
        with self.lock:
            self.stats = {
                "connections_created": 0,
                "connections_used": 0,
                "connections_returned": 0,
                "connection_errors": 0,
                "pool_errors": 0,
            }

    def close(self):
        """Close the database pool."""
        try:
            if self.pool:
                if self.db_type == "postgresql":
                    self.pool.closeall()
                elif self.db_type == "mysql":
                    self.pool.close()

                logger.info(f"Database pool closed for {self.db_type}")

        except Exception as e:
            logger.error(f"Error closing database pool: {e}")


# Global database pool instance
db_pool = None


def initialize_database_pool(db_url: Optional[str] = None) -> DatabasePool:
    """
    Initialize the global database pool.

    Args:
        db_url: Database URL (optional, uses environment variable if not provided)

    Returns:
        DatabasePool instance
    """
    global db_pool

    if db_pool:
        return db_pool

    # Parse database URL
    if not db_url:
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/smartcloudops",
        )

    # Parse URL components
    if db_url.startswith("postgresql://"):
        # PostgreSQL URL format: postgresql://user:password@host:port/database
        db_type = "postgresql"
        url_parts = db_url.replace("postgresql://", "").split("@")
        auth_parts = url_parts[0].split(":")
        host_port_db = url_parts[1].split("/")
        host_port = host_port_db[0].split(":")

        config = {
            "user": auth_parts[0],
            "password": auth_parts[1] if len(auth_parts) > 1 else "",
            "host": host_port[0],
            "port": int(host_port[1]) if len(host_port) > 1 else 5432,
            "database": host_port_db[1],
            "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", "5")),
            "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "20")),
        }

    elif db_url.startswith("mysql://"):
        # MySQL URL format: mysql://user:password@host:port/database
        db_type = "mysql"
        url_parts = db_url.replace("mysql://", "").split("@")
        auth_parts = url_parts[0].split(":")
        host_port_db = url_parts[1].split("/")
        host_port = host_port_db[0].split(":")

        config = {
            "user": auth_parts[0],
            "password": auth_parts[1] if len(auth_parts) > 1 else "",
            "host": host_port[0],
            "port": int(host_port[1]) if len(host_port) > 1 else 3306,
            "database": host_port_db[1],
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "pool_reset_session": True,
        }

    else:
        raise ValueError(f"Unsupported database URL format: {db_url}")

    # Create database pool
    db_pool = DatabasePool(db_type, **config)

    # Cache pool health status
    cache_service.set("database_pool_health", db_pool.health_check(), ttl=300)

    return db_pool


def get_database_pool() -> DatabasePool:
    """
    Get the global database pool instance.

    Returns:
        DatabasePool instance
    """
    global db_pool  # noqa: F823,F824
    if db_pool is None:
        db_pool = initialize_database_pool()
    return db_pool


# Database utility functions
def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a query using the global database pool.

    Args:
        query: SQL query to execute
        params: Query parameters

    Returns:
        Query results
    """
    pool = get_database_pool()
    return pool.execute_query(query, params)


def execute_many(query: str, params_list: List[tuple]) -> Dict[str, Any]:
    """
    Execute a query with multiple parameter sets.

    Args:
        query: SQL query to execute
        params_list: List of parameter tuples

    Returns:
        Execution results
    """
    pool = get_database_pool()
    return pool.execute_many(query, params_list)


def execute_transaction(queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute multiple queries in a transaction.

    Args:
        queries: List of query dictionaries

    Returns:
        Transaction results
    """
    pool = get_database_pool()
    return pool.execute_transaction(queries)


def check_database_health() -> Dict[str, Any]:
    """
    Check database health using the global pool.

    Returns:
        Health check results
    """
    pool = get_database_pool()
    return pool.health_check()


# Cleanup on application shutdown


def cleanup_database_pool():
    """Clean up database pool on application shutdown."""
    global db_pool  # noqa: F824
    if db_pool:
        db_pool.close()


atexit.register(cleanup_database_pool)
