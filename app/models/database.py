#!/usr/bin/env python3
"""
SmartCloudOps AI - Database Models
==================================

SQLAlchemy models for production database.
"""


import os
import time
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    permissions = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(Base):
    """API key model for secure API access."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    permissions = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class MLModel(Base):
    """ML model metadata and performance tracking."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
    s3_key = Column(String(255), nullable=True)
    accuracy = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    training_data_size = Column(Integer, nullable=True)
    training_duration = Column(Float, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prediction(Base):
    """ML prediction history and results."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, nullable=False, index=True)
    input_data = Column(JSON, nullable=False)
    prediction = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RemediationAction(Base):
    """Auto-remediation action history."""
    __tablename__ = "remediation_actions"

    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    parameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    triggered_by = Column(String(50), nullable=True)  # "manual", "automatic", "ml"
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class SystemMetric(Base):
    """System metrics for monitoring and analysis."""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)
    network_in = Column(Float, nullable=True)
    network_out = Column(Float, nullable=True)
    load_1m = Column(Float, nullable=True)
    load_5m = Column(Float, nullable=True)
    load_15m = Column(Float, nullable=True)
    response_time = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    active_connections = Column(Integer, nullable=True)
    source = Column(String(50), nullable=False, default="system")  # "system", "prometheus", "custom"


class ChatOpsCommand(Base):
    """ChatOps command history and results."""
    __tablename__ = "chatops_commands"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)
    original_input = Column(Text, nullable=False)
    cleaned_input = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False, index=True)
    entities = Column(JSON, nullable=True)
    action_plan = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="processed")
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit log for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database connection and session management


def get_database_url() -> str:
    """Get database URL from environment variables."""
    db_type = os.getenv("DATABASE_TYPE", "postgresql")

    if db_type == "postgresql":
        host = os.getenv("DATABASE_HOST", "localhost")
        port = os.getenv("DATABASE_PORT", "5432")
        name = os.getenv("DATABASE_NAME", "smartcloudops")
        user = os.getenv("DATABASE_USER", "smartcloudops_admin")
        password = os.getenv("DATABASE_PASSWORD", "")

        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            return f"postgresql://{user}@{host}:{port}/{name}"

    elif db_type == "sqlite":
        return "sqlite:///smartcloudops.db"

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def create_database_engine():
    """Create SQLAlchemy engine with proper configuration."""
    database_url = get_database_url()

    engine_kwargs = {
        "poolclass": QueuePool,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    # Add SSL configuration for PostgreSQL
    if database_url.startswith("postgresql"):
        engine_kwargs["connect_args"] = {
            "sslmode": "require" if os.getenv("DATABASE_SSL_MODE") == "require" else "prefer"
        }

    return create_engine(database_url, **engine_kwargs)


def get_database_session() -> Session:
    """Get database session."""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_database():
    """Initialize database tables."""
    engine = create_database_engine()
    Base.metadata.create_all(bind=engine)


def close_database_session(session: Session):
    """Close database session."""
    session.close()
