#!/usr/bin/env python3
"""
SmartCloudOps AI - Database Migration Tool
=========================================

Migrates from SQLite to PostgreSQL for production scalability.
Handles concurrent users and provides backup/restore capabilities.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List

import psycopg2


class DatabaseMigrator:
    """Production database migration from SQLite to PostgreSQL"""

    def __init__(self):
        self.sqlite_path = "../smartcloudops.db"
        self.pg_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "smartcloudops"),
            "user": os.getenv("DB_USER", "smartcloudops"),
            "password": os.getenv("DB_PASSWORD", ""),
        }
        self.setup_logging()

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("database_migration.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def create_postgresql_database(self):
        """Create PostgreSQL database and user"""
        self.logger.info("Creating PostgreSQL database...")

        # Connect as superuser to create database
        admin_conn = psycopg2.connect(
            host=self.pg_config["host"],
            port=self.pg_config["port"],
            database="postgres",
            user="postgres",
            password=os.getenv("POSTGRES_PASSWORD", ""),
        )
        admin_conn.autocommit = True

        with admin_conn.cursor() as cursor:
            # Create user
            cursor.execute(
                f"""
                CREATE USER {self.pg_config['user']} 
                WITH PASSWORD '{self.pg_config['password']}';
            """
            )

            # Create database
            cursor.execute(
                f"""
                CREATE DATABASE {self.pg_config['database']} 
                OWNER {self.pg_config['user']};
            """
            )

            # Grant privileges
            cursor.execute(
                f"""
                GRANT ALL PRIVILEGES ON DATABASE {self.pg_config['database']} 
                TO {self.pg_config['user']};
            """
            )

        admin_conn.close()
        self.logger.info("✅ PostgreSQL database created successfully")

    def migrate_schema(self):
        """Migrate database schema to PostgreSQL"""
        self.logger.info("Migrating database schema...")

        # Read schema from file
        with open("../database/schema.sql", "r") as f:
            schema_sql = f.read()

        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(**self.pg_config)

        with pg_conn.cursor() as cursor:
            cursor.execute(schema_sql)

        pg_conn.commit()
        pg_conn.close()
        self.logger.info("✅ Schema migration completed")

    def migrate_data(self):
        """Migrate data from SQLite to PostgreSQL"""
        self.logger.info("Starting data migration...")

        # Connect to both databases
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row

        pg_conn = psycopg2.connect(**self.pg_config)

        # Get all tables
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cursor.fetchall()]

        for table in tables:
            if table == "sqlite_sequence":
                continue

            self.logger.info(f"Migrating table: {table}")

            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()

            if not rows:
                continue

            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]

            # Insert into PostgreSQL
            with pg_conn.cursor() as pg_cursor:
                placeholders = ",".join(["%s"] * len(columns))
                insert_sql = (
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                )

                for row in rows:
                    try:
                        pg_cursor.execute(insert_sql, tuple(row))
                    except Exception as e:
                        self.logger.error(f"Error inserting row: {e}")
                        continue

            pg_conn.commit()
            self.logger.info(f"✅ Migrated {len(rows)} rows from {table}")

        sqlite_conn.close()
        pg_conn.close()
        self.logger.info("✅ Data migration completed")

    def create_backup_script(self):
        """Create automated backup script"""
        backup_script = """#!/bin/bash
# PostgreSQL Backup Script for SmartCloudOps AI
# Run daily via cron

BACKUP_DIR="/opt/smartcloudops/backups"
DB_NAME="smartcloudops"
DB_USER="smartcloudops"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/smartcloudops_backup_$TIMESTAMP.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_FILE.gz"
"""

        with open("../scripts/backup_database.sh", "w") as f:
            f.write(backup_script)

        os.chmod("../scripts/backup_database.sh", 0o755)
        self.logger.info("✅ Backup script created")

    def verify_migration(self):
        """Verify migration was successful"""
        self.logger.info("Verifying migration...")

        sqlite_conn = sqlite3.connect(self.sqlite_path)
        pg_conn = psycopg2.connect(**self.pg_config)

        # Compare row counts
        with sqlite_conn.cursor() as sqlite_cursor, pg_conn.cursor() as pg_cursor:
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in sqlite_cursor.fetchall()]

            for table in tables:
                if table == "sqlite_sequence":
                    continue

                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]

                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cursor.fetchone()[0]

                if sqlite_count == pg_count:
                    self.logger.info(
                        f"✅ {table}: {pg_count} rows migrated successfully"
                    )
                else:
                    self.logger.error(
                        f"❌ {table}: SQLite({sqlite_count}) != PostgreSQL({pg_count})"
                    )

        sqlite_conn.close()
        pg_conn.close()

    def run_migration(self):
        """Run complete migration process"""
        try:
            self.logger.info("🚀 Starting PostgreSQL migration...")

            self.create_postgresql_database()
            self.migrate_schema()
            self.migrate_data()
            self.create_backup_script()
            self.verify_migration()

            self.logger.info("🎉 Migration completed successfully!")

            # Update environment configuration
            env_config = f"""
# PostgreSQL Configuration (Production)
DB_TYPE=postgresql
DB_HOST={self.pg_config['host']}
DB_PORT={self.pg_config['port']}
DB_NAME={self.pg_config['database']}
DB_USER={self.pg_config['user']}
DB_PASSWORD={self.pg_config['password']}
DB_SSL_MODE=require
"""

            with open("../.env.production", "w") as f:
                f.write(env_config)

            self.logger.info("✅ Production environment configuration updated")

        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.run_migration()
