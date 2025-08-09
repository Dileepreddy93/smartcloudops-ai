#!/usr/bin/env python3
"""
SmartCloudOps AI - Database Models (SQLAlchemy)
==============================================

Production-ready database models with proper relationships and constraints.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, Numeric, ARRAY, JSON, ForeignKey, UniqueConstraint,
    CheckConstraint, Index, func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
import uuid
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://smartcloudops:password@localhost:5432/smartcloudops')

# Create engine with proper connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model class
Base = declarative_base()

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class User(Base, TimestampMixin):
    """User model for authentication and auditing."""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user")
    created_models = relationship("MLModelVersion", back_populates="creator")
    predictions_feedback = relationship("ModelPrediction", back_populates="feedback_provider")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'operator', 'viewer')", name='check_user_role'),
        Index('idx_users_active', 'is_active', 'created_at'),
    )
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class Metrics(Base, TimestampMixin):
    """System monitoring metrics with proper data types and constraints."""
    __tablename__ = 'metrics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    
    # CPU metrics
    cpu_usage = Column(Numeric(5, 2), nullable=False)
    
    # Memory metrics
    memory_usage = Column(Numeric(5, 2), nullable=False)
    
    # Disk metrics
    disk_usage = Column(Numeric(5, 2), nullable=False)
    
    # System load metrics
    load_1m = Column(Numeric(8, 4), nullable=False)
    load_5m = Column(Numeric(8, 4), nullable=False)
    load_15m = Column(Numeric(8, 4))
    
    # I/O metrics
    disk_io_read = Column(BigInteger, nullable=False)
    disk_io_write = Column(BigInteger, nullable=False)
    
    # Network metrics
    network_rx = Column(BigInteger, nullable=False)
    network_tx = Column(BigInteger, nullable=False)
    
    # Application metrics
    response_time = Column(Numeric(10, 3), nullable=False)
    error_rate = Column(Numeric(5, 2))
    
    # Anomaly detection
    is_anomaly = Column(Boolean, nullable=False, default=False)
    anomaly_score = Column(Numeric(5, 4))
    
    # Audit fields
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User")
    predictions = relationship("ModelPrediction", back_populates="metrics")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('cpu_usage >= 0 AND cpu_usage <= 100', name='check_cpu_usage'),
        CheckConstraint('memory_usage >= 0 AND memory_usage <= 100', name='check_memory_usage'),
        CheckConstraint('disk_usage >= 0 AND disk_usage <= 100', name='check_disk_usage'),
        CheckConstraint('load_1m >= 0', name='check_load_1m'),
        CheckConstraint('load_5m >= 0', name='check_load_5m'),
        CheckConstraint('load_15m >= 0', name='check_load_15m'),
        CheckConstraint('disk_io_read >= 0', name='check_disk_io_read'),
        CheckConstraint('disk_io_write >= 0', name='check_disk_io_write'),
        CheckConstraint('network_rx >= 0', name='check_network_rx'),
        CheckConstraint('network_tx >= 0', name='check_network_tx'),
        CheckConstraint('response_time >= 0', name='check_response_time'),
        CheckConstraint('error_rate >= 0 AND error_rate <= 100', name='check_error_rate'),
        CheckConstraint('anomaly_score >= 0 AND anomaly_score <= 1', name='check_anomaly_score'),
        Index('idx_metrics_timestamp', 'timestamp'),
        Index('idx_metrics_source_time', 'source', 'timestamp'),
        Index('idx_metrics_anomaly', 'is_anomaly', 'timestamp'),
        Index('idx_metrics_timeseries', 'source', 'timestamp', 'cpu_usage', 'memory_usage', 'is_anomaly'),
    )
    
    def __repr__(self):
        return f"<Metrics(timestamp='{self.timestamp}', source='{self.source}', anomaly={self.is_anomaly})>"

class MLModel(Base, TimestampMixin):
    """ML model definitions and metadata."""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, unique=True)
    model_type = Column(String(50), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship("User")
    versions = relationship("MLModelVersion", back_populates="model", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("model_type IN ('isolation_forest', 'prophet', 'rule_based', 'ensemble')", name='check_model_type'),
        Index('idx_ml_models_active', 'is_active', 'created_at'),
    )
    
    def __repr__(self):
        return f"<MLModel(name='{self.model_name}', type='{self.model_type}', active={self.is_active})>"

class MLModelVersion(Base, TimestampMixin):
    """Version control for ML models with performance tracking."""
    __tablename__ = 'ml_model_versions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey('ml_models.id', ondelete='CASCADE'), nullable=False)
    version = Column(String(20), nullable=False)
    training_timestamp = Column(DateTime(timezone=True), nullable=False)
    training_data_start = Column(DateTime(timezone=True), nullable=False)
    training_data_end = Column(DateTime(timezone=True), nullable=False)
    training_data_size = Column(Integer, nullable=False)
    
    # Model configuration
    model_config = Column(JSONB, nullable=False)
    thresholds = Column(JSONB, nullable=False)
    
    # Performance metrics
    accuracy = Column(Numeric(5, 4))
    precision_score = Column(Numeric(5, 4))
    recall_score = Column(Numeric(5, 4))
    f1_score = Column(Numeric(5, 4))
    
    # Model artifacts
    model_path = Column(String(500))
    scaler_path = Column(String(500))
    
    # Status tracking
    status = Column(String(20), nullable=False, default='training')
    is_deployed = Column(Boolean, nullable=False, default=False)
    deployment_notes = Column(Text)
    
    # Audit fields
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Relationships
    model = relationship("MLModel", back_populates="versions")
    creator = relationship("User", back_populates="created_models")
    predictions = relationship("ModelPrediction", back_populates="model_version")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('model_id', 'version', name='uq_model_version'),
        CheckConstraint('training_data_size > 0', name='check_training_data_size'),
        CheckConstraint('accuracy >= 0 AND accuracy <= 1', name='check_accuracy'),
        CheckConstraint('precision_score >= 0 AND precision_score <= 1', name='check_precision'),
        CheckConstraint('recall_score >= 0 AND recall_score <= 1', name='check_recall'),
        CheckConstraint('f1_score >= 0 AND f1_score <= 1', name='check_f1_score'),
        CheckConstraint("status IN ('training', 'ready', 'deployed', 'deprecated')", name='check_status'),
        Index('idx_ml_model_versions_deployed', 'is_deployed', 'model_id'),
        Index('idx_ml_model_versions_status', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<MLModelVersion(model_id={self.model_id}, version='{self.version}', status='{self.status}')>"

class APIKey(Base, TimestampMixin):
    """API key management with usage tracking and rate limiting."""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    permissions = Column(ARRAY(String), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    description = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(BigInteger, nullable=False, default=0)
    rate_limit_per_hour = Column(Integer, default=1000)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    user = relationship("User", back_populates="api_keys", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    usage_logs = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index('idx_api_keys_user', 'user_id', 'is_active'),
        Index('idx_api_keys_active', 'is_active', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<APIKey(name='{self.key_name}', active={self.is_active})>"

class APIKeyUsage(Base):
    """API key usage tracking for monitoring and rate limiting."""
    __tablename__ = 'api_key_usage'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    api_key_id = Column(Integer, ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer)
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    
    # Constraints
    __table_args__ = (
        Index('idx_api_usage_key_time', 'api_key_id', 'created_at'),
        Index('idx_api_usage_endpoint', 'endpoint', 'created_at'),
        Index('idx_api_usage_time', 'created_at'),
    )
    
    def __repr__(self):
        return f"<APIKeyUsage(api_key_id={self.api_key_id}, endpoint='{self.endpoint}')>"

class ModelPrediction(Base):
    """Model predictions for tracking and analysis."""
    __tablename__ = 'model_predictions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    model_version_id = Column(Integer, ForeignKey('ml_model_versions.id'), nullable=False)
    metrics_id = Column(BigInteger, ForeignKey('metrics.id'))
    predicted_anomaly = Column(Boolean, nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    prediction_time_ms = Column(Integer, nullable=False)
    model_features = Column(JSONB)
    actual_anomaly = Column(Boolean)  # For feedback learning
    feedback_provided_at = Column(DateTime(timezone=True))
    feedback_provided_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    model_version = relationship("MLModelVersion", back_populates="predictions")
    metrics = relationship("Metrics", back_populates="predictions")
    feedback_provider = relationship("User", back_populates="predictions_feedback")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score'),
        CheckConstraint('prediction_time_ms >= 0', name='check_prediction_time'),
        Index('idx_predictions_model_time', 'model_version_id', 'created_at'),
        Index('idx_predictions_anomaly', 'predicted_anomaly', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ModelPrediction(model_version_id={self.model_version_id}, anomaly={self.predicted_anomaly})>"

class AnomalyPrediction(Base):
    """Anomaly predictions summary for faster queries."""
    __tablename__ = 'anomaly_predictions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(100), nullable=False)
    anomaly_detected = Column(Boolean, nullable=False)
    severity = Column(String(20))
    confidence_score = Column(Numeric(5, 4), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    alert_sent = Column(Boolean, nullable=False, default=False)
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    acknowledged_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    acknowledger = relationship("User")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name='check_severity'),
        Index('idx_anomaly_predictions_time', 'timestamp'),
        Index('idx_anomaly_predictions_unack', 'acknowledged', 'severity', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AnomalyPrediction(timestamp='{self.timestamp}', severity='{self.severity}')>"

# Database utilities
def get_session() -> Session:
    """Get database session."""
    return SessionLocal()

def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False

def drop_tables():
    """Drop all database tables."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Database tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error dropping database tables: {e}")
        return False

def init_database():
    """Initialize database with default data."""
    try:
        session = get_session()
        
        # Create default admin user if not exists
        admin_user = session.query(User).filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@smartcloudops.ai',
                role='admin'
            )
            session.add(admin_user)
        
        # Create system user if not exists
        system_user = session.query(User).filter_by(username='system').first()
        if not system_user:
            system_user = User(
                username='system',
                email='system@smartcloudops.ai',
                role='admin'
            )
            session.add(system_user)
        
        session.commit()
        session.close()
        logger.info("✅ Database initialized with default data")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ SmartCloudOps AI - Database Models")
    print("=====================================")
    
    # Test database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Database connected: {version[0]}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)
    
    # Create tables
    if create_tables():
        print("✅ Tables created successfully")
    else:
        print("❌ Failed to create tables")
        exit(1)
    
    # Initialize with default data
    if init_database():
        print("✅ Database initialized successfully")
    else:
        print("❌ Failed to initialize database")
        exit(1)
    
    print("\n🎉 Database setup complete!")
