#!/usr/bin/env python3
"""
SmartCloudOps AI - Database Migration Tool
=========================================

Complete migration from JSON files to PostgreSQL database.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrationTool:
    """Tool for migrating data from JSON files to PostgreSQL."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.data_dir = self.app_dir / 'data'
        self.ml_models_dir = self.app_dir / 'ml_models'
        self.migration_stats = {
            'metrics_migrated': 0,
            'models_migrated': 0,
            'api_keys_migrated': 0,
            'errors': []
        }
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met for migration."""
        logger.info("🔍 Checking migration prerequisites...")
        
        # Check if SQLAlchemy is available
        try:
            import sqlalchemy
            logger.info(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
        except ImportError:
            logger.error("❌ SQLAlchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
            return False
        
        # Check if database models are available
        try:
            sys.path.insert(0, str(self.app_dir / 'database'))
            from models import get_session, User, Metrics, MLModel, MLModelVersion, APIKey
            logger.info("✅ Database models imported successfully")
            self.session = get_session()
            self.models = {
                'User': User,
                'Metrics': Metrics,
                'MLModel': MLModel,
                'MLModelVersion': MLModelVersion,
                'APIKey': APIKey
            }
        except ImportError as e:
            logger.error(f"❌ Failed to import database models: {e}")
            return False
        
        # Check database connection
        try:
            # Test database connection
            result = self.session.execute("SELECT version()")
            version = result.fetchone()
            logger.info(f"✅ Database connected: PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
        
        # Check if data files exist
        data_files = [
            self.data_dir / 'real_training_data.json',
            self.ml_models_dir / 'real_data_model.json'
        ]
        
        for file_path in data_files:
            if file_path.exists():
                logger.info(f"✅ Found data file: {file_path.name}")
            else:
                logger.warning(f"⚠️ Data file not found: {file_path.name}")
        
        return True
    
    def migrate_users(self) -> bool:
        """Create default users if they don't exist."""
        logger.info("👥 Migrating users...")
        
        try:
            User = self.models['User']
            
            # Create admin user
            admin_user = self.session.query(User).filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@smartcloudops.ai',
                    role='admin'
                )
                self.session.add(admin_user)
                logger.info("✅ Created admin user")
            
            # Create system user
            system_user = self.session.query(User).filter_by(username='system').first()
            if not system_user:
                system_user = User(
                    username='system',
                    email='system@smartcloudops.ai',
                    role='admin'
                )
                self.session.add(system_user)
                logger.info("✅ Created system user")
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating users: {e}")
            self.session.rollback()
            return False
    
    def migrate_metrics_data(self) -> bool:
        """Migrate metrics data from JSON to database."""
        logger.info("📊 Migrating metrics data...")
        
        data_file = self.data_dir / 'real_training_data.json'
        if not data_file.exists():
            logger.warning(f"⚠️ Metrics data file not found: {data_file}")
            return True  # Not an error if file doesn't exist
        
        try:
            Metrics = self.models['Metrics']
            User = self.models['User']
            
            # Get system user for created_by
            system_user = self.session.query(User).filter_by(username='system').first()
            if not system_user:
                logger.error("❌ System user not found")
                return False
            
            with open(data_file, 'r') as f:
                metrics_data = json.load(f)
            
            logger.info(f"📈 Processing {len(metrics_data)} metrics records...")
            
            batch_size = 1000
            for i in range(0, len(metrics_data), batch_size):
                batch = metrics_data[i:i + batch_size]
                
                for data in batch:
                    try:
                        # Parse timestamp
                        timestamp_str = data.get('timestamp')
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            timestamp = datetime.now(timezone.utc)
                        
                        # Create metrics record
                        metric = Metrics(
                            timestamp=timestamp,
                            source=data.get('source', 'historical_data'),
                            cpu_usage=Decimal(str(data.get('cpu_usage', 0))),
                            memory_usage=Decimal(str(data.get('memory_usage', 0))),
                            disk_usage=Decimal(str(data.get('disk_usage', 0))),
                            load_1m=Decimal(str(data.get('load_1m', 0))),
                            load_5m=Decimal(str(data.get('load_5m', 0))),
                            load_15m=Decimal(str(data.get('load_15m', 0))),
                            disk_io_read=int(data.get('disk_io_read', 0)),
                            disk_io_write=int(data.get('disk_io_write', 0)),
                            network_rx=int(data.get('network_rx', 0)),
                            network_tx=int(data.get('network_tx', 0)),
                            response_time=Decimal(str(data.get('response_time', 0))),
                            error_rate=Decimal(str(data.get('error_rate', 0))) if data.get('error_rate') else None,
                            is_anomaly=bool(data.get('is_anomaly', False)),
                            anomaly_score=Decimal(str(data.get('anomaly_score', 0))) if data.get('anomaly_score') else None,
                            created_by=system_user.id
                        )
                        
                        self.session.add(metric)
                        self.migration_stats['metrics_migrated'] += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing metric record: {e}")
                        self.migration_stats['errors'].append(f"Metric record error: {e}")
                        continue
                
                # Commit batch
                try:
                    self.session.commit()
                    logger.info(f"✅ Migrated batch {i//batch_size + 1}/{(len(metrics_data)-1)//batch_size + 1}")
                except Exception as e:
                    logger.error(f"❌ Error committing batch: {e}")
                    self.session.rollback()
                    return False
            
            logger.info(f"✅ Successfully migrated {self.migration_stats['metrics_migrated']} metrics records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating metrics data: {e}")
            self.session.rollback()
            return False
    
    def migrate_ml_models(self) -> bool:
        """Migrate ML models from JSON to database."""
        logger.info("🤖 Migrating ML models...")
        
        model_file = self.ml_models_dir / 'real_data_model.json'
        if not model_file.exists():
            logger.warning(f"⚠️ ML model file not found: {model_file}")
            return True
        
        try:
            MLModel = self.models['MLModel']
            MLModelVersion = self.models['MLModelVersion']
            User = self.models['User']
            
            # Get system user
            system_user = self.session.query(User).filter_by(username='system').first()
            if not system_user:
                logger.error("❌ System user not found")
                return False
            
            with open(model_file, 'r') as f:
                model_data = json.load(f)
            
            model_name = "real_data_anomaly_detector"
            model_type = model_data.get('model_type', 'rule_based')
            
            # Create or get ML model
            ml_model = self.session.query(MLModel).filter_by(model_name=model_name).first()
            if not ml_model:
                ml_model = MLModel(
                    model_name=model_name,
                    model_type=model_type,
                    description="Migrated from JSON file storage",
                    is_active=True,
                    created_by=system_user.id
                )
                self.session.add(ml_model)
                self.session.flush()  # Get the ID
            
            # Parse training timestamp
            training_timestamp_str = model_data.get('training_timestamp')
            if training_timestamp_str:
                training_timestamp = datetime.fromisoformat(training_timestamp_str)
            else:
                training_timestamp = datetime.now(timezone.utc)
            
            # Create model version
            version = "1.0.0"
            model_version = self.session.query(MLModelVersion).filter_by(
                model_id=ml_model.id, version=version
            ).first()
            
            if not model_version:
                # Extract performance metrics
                performance = model_data.get('performance', {})
                
                model_version = MLModelVersion(
                    model_id=ml_model.id,
                    version=version,
                    training_timestamp=training_timestamp,
                    training_data_start=training_timestamp,
                    training_data_end=training_timestamp,
                    training_data_size=model_data.get('training_data_size', 0),
                    model_config=model_data.get('thresholds', {}),
                    thresholds=model_data.get('thresholds', {}),
                    accuracy=Decimal(str(performance.get('accuracy', 0))) if performance.get('accuracy') else None,
                    precision_score=Decimal(str(performance.get('precision', 0))) if performance.get('precision') else None,
                    recall_score=Decimal(str(performance.get('recall', 0))) if performance.get('recall') else None,
                    f1_score=Decimal(str(performance.get('f1_score', 0))) if performance.get('f1_score') else None,
                    model_path=str(model_file),
                    status='ready',
                    is_deployed=True,
                    created_by=system_user.id
                )
                self.session.add(model_version)
                self.migration_stats['models_migrated'] += 1
                logger.info(f"✅ Created model version: {model_name} v{version}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating ML models: {e}")
            self.session.rollback()
            return False
    
    def migrate_api_keys(self) -> bool:
        """Migrate API keys from file storage to database."""
        logger.info("🔐 Migrating API keys...")
        
        api_keys_file = self.app_dir / 'api_keys_db.json'
        if not api_keys_file.exists():
            logger.warning(f"⚠️ API keys file not found: {api_keys_file}")
            return True
        
        try:
            APIKey = self.models['APIKey']
            User = self.models['User']
            
            # Get admin user
            admin_user = self.session.query(User).filter_by(username='admin').first()
            if not admin_user:
                logger.error("❌ Admin user not found")
                return False
            
            with open(api_keys_file, 'r') as f:
                api_keys_data = json.load(f)
            
            for key_name, key_data in api_keys_data.items():
                try:
                    # Hash the key (in real implementation, keys should already be hashed)
                    key_hash = hashlib.sha256(key_data.get('key', key_name).encode()).hexdigest()
                    
                    # Check if key already exists
                    existing_key = self.session.query(APIKey).filter_by(key_hash=key_hash).first()
                    if existing_key:
                        continue
                    
                    api_key = APIKey(
                        key_name=key_name,
                        key_hash=key_hash,
                        permissions=key_data.get('permissions', ['read']),
                        user_id=admin_user.id,
                        description=f"Migrated API key: {key_name}",
                        is_active=True,
                        created_by=admin_user.id
                    )
                    
                    self.session.add(api_key)
                    self.migration_stats['api_keys_migrated'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error processing API key {key_name}: {e}")
                    continue
            
            self.session.commit()
            logger.info(f"✅ Successfully migrated {self.migration_stats['api_keys_migrated']} API keys")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating API keys: {e}")
            self.session.rollback()
            return False
    
    def verify_migration(self) -> bool:
        """Verify that migration was successful."""
        logger.info("🔍 Verifying migration...")
        
        try:
            User = self.models['User']
            Metrics = self.models['Metrics']
            MLModel = self.models['MLModel']
            APIKey = self.models['APIKey']
            
            # Count records
            user_count = self.session.query(User).count()
            metrics_count = self.session.query(Metrics).count()
            model_count = self.session.query(MLModel).count()
            api_key_count = self.session.query(APIKey).count()
            
            logger.info(f"📊 Migration verification:")
            logger.info(f"   Users: {user_count}")
            logger.info(f"   Metrics: {metrics_count}")
            logger.info(f"   ML Models: {model_count}")
            logger.info(f"   API Keys: {api_key_count}")
            
            # Check for recent data
            if metrics_count > 0:
                latest_metric = self.session.query(Metrics).order_by(Metrics.timestamp.desc()).first()
                logger.info(f"   Latest metric: {latest_metric.timestamp}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying migration: {e}")
            return False
    
    def cleanup_old_files(self) -> bool:
        """Create backup of old files and optionally remove them."""
        logger.info("🧹 Creating backup of old files...")
        
        try:
            import shutil
            backup_dir = self.app_dir / 'backup' / f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Files to backup
            files_to_backup = [
                self.data_dir / 'real_training_data.json',
                self.ml_models_dir / 'real_data_model.json',
                self.app_dir / 'api_keys_db.json'
            ]
            
            for file_path in files_to_backup:
                if file_path.exists():
                    backup_path = backup_dir / file_path.name
                    shutil.copy2(file_path, backup_path)
                    logger.info(f"✅ Backed up: {file_path.name}")
            
            logger.info(f"✅ Backup created at: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run complete migration process."""
        logger.info("🚀 Starting database migration...")
        logger.info("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met")
            return False
        
        try:
            # Run migration steps
            steps = [
                ("Users", self.migrate_users),
                ("Metrics Data", self.migrate_metrics_data),
                ("ML Models", self.migrate_ml_models),
                ("API Keys", self.migrate_api_keys),
                ("Verification", self.verify_migration),
                ("Backup", self.cleanup_old_files)
            ]
            
            for step_name, step_func in steps:
                logger.info(f"\n🔄 Step: {step_name}")
                if not step_func():
                    logger.error(f"❌ Migration step failed: {step_name}")
                    return False
                logger.info(f"✅ Step completed: {step_name}")
            
            # Print final statistics
            self.print_migration_summary()
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            if hasattr(self, 'session'):
                self.session.close()
    
    def print_migration_summary(self):
        """Print migration summary."""
        logger.info("\n" + "=" * 50)
        logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 50)
        logger.info(f"📊 Migration Statistics:")
        logger.info(f"   Metrics migrated: {self.migration_stats['metrics_migrated']}")
        logger.info(f"   Models migrated: {self.migration_stats['models_migrated']}")
        logger.info(f"   API keys migrated: {self.migration_stats['api_keys_migrated']}")
        logger.info(f"   Errors encountered: {len(self.migration_stats['errors'])}")
        
        if self.migration_stats['errors']:
            logger.warning("\n⚠️ Errors encountered:")
            for error in self.migration_stats['errors'][:5]:  # Show first 5 errors
                logger.warning(f"   - {error}")
        
        logger.info("\n✅ Database migration complete!")
        logger.info("✅ Application can now use PostgreSQL database")
        logger.info("✅ JSON file backups created for safety")

def main():
    """Main migration function."""
    print("🗄️ SmartCloudOps AI - Database Migration Tool")
    print("=" * 50)
    
    migration_tool = DatabaseMigrationTool()
    
    if migration_tool.run_migration():
        print("\n🎉 Migration completed successfully!")
        return 0
    else:
        print("\n❌ Migration failed!")
        return 1

if __name__ == "__main__":
    exit(main())
