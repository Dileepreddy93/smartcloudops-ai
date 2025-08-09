#!/usr/bin/env python3
"""
SmartCloudOps AI - Database Models (SQLite Version)
==================================================

Production-ready database models with SQLite for development/testing.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import sqlite3
import json
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for SmartCloudOps AI."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            app_dir = Path(__file__).parent.parent
            db_path = str(app_dir / 'database' / 'smartcloudops.db')
        
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn
    
    def init_database(self):
        """Initialize database with all tables."""
        logger.info("🗄️ Initializing SQLite database...")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create tables
                self.create_users_table(cursor)
                self.create_metrics_table(cursor)
                self.create_ml_models_table(cursor)
                self.create_ml_model_versions_table(cursor)
                self.create_api_keys_table(cursor)
                self.create_api_key_usage_table(cursor)
                self.create_model_predictions_table(cursor)
                self.create_anomaly_predictions_table(cursor)
                
                # Create indexes
                self.create_indexes(cursor)
                
                # Create initial data
                self.create_initial_data(cursor)
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise
    
    def create_users_table(self, cursor):
        """Create users table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_metrics_table(self, cursor):
        """Create metrics table with proper constraints."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                source TEXT NOT NULL,
                cpu_usage REAL NOT NULL CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
                memory_usage REAL NOT NULL CHECK (memory_usage >= 0 AND memory_usage <= 100),
                disk_usage REAL NOT NULL CHECK (disk_usage >= 0 AND disk_usage <= 100),
                load_1m REAL NOT NULL CHECK (load_1m >= 0),
                load_5m REAL NOT NULL CHECK (load_5m >= 0),
                load_15m REAL CHECK (load_15m >= 0),
                disk_io_read INTEGER NOT NULL CHECK (disk_io_read >= 0),
                disk_io_write INTEGER NOT NULL CHECK (disk_io_write >= 0),
                network_rx INTEGER NOT NULL CHECK (network_rx >= 0),
                network_tx INTEGER NOT NULL CHECK (network_tx >= 0),
                response_time REAL NOT NULL CHECK (response_time >= 0),
                error_rate REAL CHECK (error_rate >= 0 AND error_rate <= 100),
                is_anomaly BOOLEAN NOT NULL DEFAULT 0,
                anomaly_score REAL CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT REFERENCES users(id)
            )
        """)
    
    def create_ml_models_table(self, cursor):
        """Create ML models table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL UNIQUE,
                model_type TEXT NOT NULL CHECK (model_type IN ('isolation_forest', 'prophet', 'rule_based', 'ensemble')),
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL REFERENCES users(id),
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_ml_model_versions_table(self, cursor):
        """Create ML model versions table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
                version TEXT NOT NULL,
                training_timestamp TIMESTAMP NOT NULL,
                training_data_start TIMESTAMP NOT NULL,
                training_data_end TIMESTAMP NOT NULL,
                training_data_size INTEGER NOT NULL CHECK (training_data_size > 0),
                model_config TEXT NOT NULL,  -- JSON string
                thresholds TEXT NOT NULL,    -- JSON string
                accuracy REAL CHECK (accuracy >= 0 AND accuracy <= 1),
                precision_score REAL CHECK (precision_score >= 0 AND precision_score <= 1),
                recall_score REAL CHECK (recall_score >= 0 AND recall_score <= 1),
                f1_score REAL CHECK (f1_score >= 0 AND f1_score <= 1),
                model_path TEXT,
                scaler_path TEXT,
                status TEXT NOT NULL DEFAULT 'training' CHECK (status IN ('training', 'ready', 'deployed', 'deprecated')),
                is_deployed BOOLEAN NOT NULL DEFAULT 0,
                deployment_notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL REFERENCES users(id),
                UNIQUE(model_id, version)
            )
        """)
    
    def create_api_keys_table(self, cursor):
        """Create API keys table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                permissions TEXT NOT NULL,  -- JSON array
                user_id TEXT REFERENCES users(id),
                description TEXT,
                expires_at TIMESTAMP,
                last_used_at TIMESTAMP,
                usage_count INTEGER NOT NULL DEFAULT 0,
                rate_limit_per_hour INTEGER DEFAULT 1000,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT REFERENCES users(id),
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_api_key_usage_table(self, cursor):
        """Create API key usage table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_key_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_id INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                response_time_ms INTEGER,
                request_size_bytes INTEGER,
                response_size_bytes INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_model_predictions_table(self, cursor):
        """Create model predictions table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version_id INTEGER NOT NULL REFERENCES ml_model_versions(id),
                metrics_id INTEGER REFERENCES metrics(id),
                predicted_anomaly BOOLEAN NOT NULL,
                confidence_score REAL NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
                prediction_time_ms INTEGER NOT NULL CHECK (prediction_time_ms >= 0),
                model_features TEXT,  -- JSON string
                actual_anomaly BOOLEAN,
                feedback_provided_at TIMESTAMP,
                feedback_provided_by TEXT REFERENCES users(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_anomaly_predictions_table(self, cursor):
        """Create anomaly predictions summary table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                source TEXT NOT NULL,
                anomaly_detected BOOLEAN NOT NULL,
                severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
                confidence_score REAL NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                alert_sent BOOLEAN NOT NULL DEFAULT 0,
                acknowledged BOOLEAN NOT NULL DEFAULT 0,
                acknowledged_by TEXT REFERENCES users(id),
                acknowledged_at TIMESTAMP,
                resolution_notes TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def create_indexes(self, cursor):
        """Create performance indexes."""
        indexes = [
            # Metrics indexes
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics (timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_source_time ON metrics (source, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_anomaly ON metrics (is_anomaly, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_created_at ON metrics (created_at DESC)",
            
            # ML Models indexes
            "CREATE INDEX IF NOT EXISTS idx_ml_models_active ON ml_models (is_active, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_ml_model_versions_deployed ON ml_model_versions (is_deployed, model_id)",
            "CREATE INDEX IF NOT EXISTS idx_ml_model_versions_status ON ml_model_versions (status, created_at DESC)",
            
            # API Keys indexes
            "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys (key_hash)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys (user_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys (is_active, expires_at)",
            
            # Usage indexes
            "CREATE INDEX IF NOT EXISTS idx_api_usage_key_time ON api_key_usage (api_key_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_key_usage (endpoint, created_at DESC)",
            
            # Predictions indexes
            "CREATE INDEX IF NOT EXISTS idx_predictions_model_time ON model_predictions (model_version_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_anomaly ON model_predictions (predicted_anomaly, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_time ON anomaly_predictions (timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_unack ON anomaly_predictions (acknowledged, severity, timestamp DESC)"
        ]
        
        for index in indexes:
            cursor.execute(index)
    
    def create_initial_data(self, cursor):
        """Create initial users and data."""
        import uuid
        
        # Create admin user
        admin_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT OR IGNORE INTO users (id, username, email, role)
            VALUES (?, 'admin', 'admin@smartcloudops.ai', 'admin')
        """, (admin_id,))
        
        # Create system user
        system_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT OR IGNORE INTO users (id, username, email, role)
            VALUES (?, 'system', 'system@smartcloudops.ai', 'admin')
        """, (system_id,))
    
    def migrate_json_data(self):
        """Migrate data from JSON files to database."""
        logger.info("🔄 Starting data migration from JSON files...")
        
        app_dir = Path(__file__).parent.parent
        migrated_count = 0
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get system user
                cursor.execute("SELECT id FROM users WHERE username = 'system'")
                system_user = cursor.fetchone()
                if not system_user:
                    logger.error("❌ System user not found")
                    return False
                system_user_id = system_user['id']
                
                # Migrate metrics data
                metrics_file = app_dir / 'data' / 'real_training_data.json'
                if metrics_file.exists():
                    logger.info(f"📊 Migrating metrics from {metrics_file}")
                    
                    with open(metrics_file, 'r') as f:
                        metrics_data = json.load(f)
                    
                    for data in metrics_data:
                        try:
                            cursor.execute("""
                                INSERT INTO metrics (
                                    timestamp, source, cpu_usage, memory_usage, disk_usage,
                                    load_1m, load_5m, disk_io_read, disk_io_write,
                                    network_rx, network_tx, response_time, is_anomaly,
                                    created_by
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                data.get('timestamp'),
                                data.get('source', 'historical_data'),
                                data.get('cpu_usage', 0),
                                data.get('memory_usage', 0),
                                data.get('disk_usage', 0),
                                data.get('load_1m', 0),
                                data.get('load_5m', 0),
                                data.get('disk_io_read', 0),
                                data.get('disk_io_write', 0),
                                data.get('network_rx', 0),
                                data.get('network_tx', 0),
                                data.get('response_time', 0),
                                bool(data.get('is_anomaly', False)),
                                system_user_id
                            ))
                            migrated_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️ Error migrating metric: {e}")
                            continue
                    
                    logger.info(f"✅ Migrated {migrated_count} metrics records")
                
                # Migrate ML model
                model_file = app_dir / 'ml_models' / 'real_data_model.json'
                if model_file.exists():
                    logger.info(f"🤖 Migrating ML model from {model_file}")
                    
                    with open(model_file, 'r') as f:
                        model_data = json.load(f)
                    
                    # Create ML model
                    cursor.execute("""
                        INSERT OR IGNORE INTO ml_models (model_name, model_type, description, is_active, created_by)
                        VALUES ('real_data_anomaly_detector', ?, 'Migrated from JSON storage', 1, ?)
                    """, (model_data.get('model_type', 'rule_based'), system_user_id))
                    
                    # Get model ID
                    cursor.execute("SELECT id FROM ml_models WHERE model_name = 'real_data_anomaly_detector'")
                    model_row = cursor.fetchone()
                    if model_row:
                        model_id = model_row['id']
                        
                        # Create model version
                        performance = model_data.get('performance', {})
                        cursor.execute("""
                            INSERT OR IGNORE INTO ml_model_versions (
                                model_id, version, training_timestamp, training_data_start,
                                training_data_end, training_data_size, model_config, thresholds,
                                accuracy, precision_score, recall_score, f1_score,
                                model_path, status, is_deployed, created_by
                            ) VALUES (?, '1.0.0', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready', 1, ?)
                        """, (
                            model_id,
                            model_data.get('training_timestamp', datetime.now().isoformat()),
                            model_data.get('training_timestamp', datetime.now().isoformat()),
                            model_data.get('training_timestamp', datetime.now().isoformat()),
                            model_data.get('training_data_size', 0),
                            json.dumps(model_data.get('thresholds', {})),
                            json.dumps(model_data.get('thresholds', {})),
                            performance.get('accuracy'),
                            performance.get('precision'),
                            performance.get('recall'),
                            performance.get('f1_score'),
                            str(model_file),
                            system_user_id
                        ))
                        
                        logger.info("✅ Migrated ML model")
                
                conn.commit()
                logger.info(f"🎉 Migration completed! Migrated {migrated_count} records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Migration error: {e}")
            return False
    
    def get_stats(self):
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                tables = ['users', 'metrics', 'ml_models', 'ml_model_versions', 'api_keys']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    stats[table] = result['count'] if result else 0
                
                return stats
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

# Database instance
db_manager = DatabaseManager()

def get_db():
    """Get database connection."""
    return db_manager.get_connection()

def migrate_data():
    """Run data migration."""
    return db_manager.migrate_json_data()

def get_database_stats():
    """Get database statistics."""
    return db_manager.get_stats()

if __name__ == "__main__":
    print("🗄️ SmartCloudOps AI - SQLite Database Models")
    print("=" * 50)
    
    # Initialize database
    print("✅ Database initialized")
    
    # Run migration
    if migrate_data():
        print("✅ Data migration completed")
    else:
        print("⚠️ Data migration had issues")
    
    # Show statistics
    stats = get_database_stats()
    print(f"\n📊 Database Statistics:")
    for table, count in stats.items():
        print(f"   {table}: {count} records")
    
    print("\n🎉 Database setup complete!")
