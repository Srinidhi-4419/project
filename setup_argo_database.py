#!/usr/bin/env python3
"""
Argo Float Database Setup Script
This script creates and initializes the complete Argo float database schema
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from pathlib import Path
from configparser import ConfigParser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(filename='database.ini', section='database'):
    """Load database configuration from ini file"""
    parser = ConfigParser()
    parser.read(filename)

    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')

    return config

class ArgoFloatDatabaseSetup:
    def __init__(self, admin_config, target_db_config):
        """
        Initialize database setup

        Args:
            admin_config (dict): Admin connection config for creating database
            target_db_config (dict): Target database configuration
        """
        self.admin_config = admin_config
        self.target_db_config = target_db_config
        self.schema_file = 'argo_float_schema.sql'

    def create_database(self):
        """Create the target database if it doesn't exist"""
        try:
            # Connect to PostgreSQL with admin privileges
            conn = psycopg2.connect(**self.admin_config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.target_db_config['database'],)
            )

            if cursor.fetchone():
                logger.info(f"Database '{self.target_db_config['database']}' already exists")
            else:
                # Create database
                cursor.execute(f"CREATE DATABASE {self.target_db_config['database']}")
                logger.info(f"Database '{self.target_db_config['database']}' created successfully")

            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise

    def run_schema_script(self):
        """Execute the schema SQL script"""
        try:
            # Connect to target database
            conn = psycopg2.connect(**self.target_db_config)
            cursor = conn.cursor()

            # Read and execute schema file
            if not os.path.exists(self.schema_file):
                raise FileNotFoundError(f"Schema file '{self.schema_file}' not found")

            with open(self.schema_file, 'r') as f:
                schema_sql = f.read()

            logger.info("Executing schema script...")
            cursor.execute(schema_sql)
            conn.commit()

            logger.info("Schema created successfully!")

            # Verify tables were created
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)

            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Created {len(tables)} tables:")
            for table in tables:
                logger.info(f"  ✓ {table}")

            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error executing schema: {e}")
            raise

    def test_connection(self):
        """Test database connection and basic queries"""
        try:
            conn = psycopg2.connect(**self.target_db_config)
            cursor = conn.cursor()

            # Test query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            logger.info(f"Connected to: {version}")

            # Test table access
            cursor.execute("SELECT count(*) FROM qc_flags_table;")
            qc_count = cursor.fetchone()[0]
            logger.info(f"QC flags table contains {qc_count} records")

            cursor.close()
            conn.close()
            logger.info("Database connection test successful!")

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise

    def setup_complete_database(self):
        """Run complete database setup process"""
        logger.info("Starting Argo Float Database Setup...")

        try:
            # Step 1: Create database
            self.create_database()

            # Step 2: Run schema script
            self.run_schema_script()

            # Step 3: Test connection
            self.test_connection()

            logger.info("✅ Argo Float Database setup completed successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False

def main():
    """Main execution function"""

    try:
        # Load database configuration from ini file
        logger.info("Loading database configuration from database.ini...")
        db_config = load_config('database.ini', 'database')

        # Configuration for admin connection (to create database)
        admin_config = {
            'host': db_config['host'],
            'port': int(db_config['port']),
            'user': db_config['user'],
            'password': db_config['password'],
            'database': 'postgres'  # Connect to default postgres database
        }

        # Configuration for target database
        target_db_config = {
            'host': db_config['host'],
            'port': int(db_config['port']),
            'user': db_config['user'],
            'password': db_config['password'],
            'database': 'argo_floats'  # Target database name
        }

        logger.info(f"Connecting to PostgreSQL at {db_config['host']}:{db_config['port']} as user '{db_config['user']}'")

        # Create and run setup
        setup = ArgoFloatDatabaseSetup(admin_config, target_db_config)

        if setup.setup_complete_database():
            print("\n🎉 Setup completed! You can now:")
            print("  • Connect to database 'argo_floats'")
            print("  • Start importing Argo float data")
            print("  • Run queries on the schema")
        else:
            print("\n❌ Setup failed. Check logs for details.")
            sys.exit(1)

    except FileNotFoundError:
        logger.error("❌ database.ini file not found!")
        logger.error("Please create database.ini with your PostgreSQL credentials")
        print("\nCreate database.ini file with:")
        print("[database]")
        print("host = localhost")
        print("port = 5432")
        print("user = postgres")
        print("password = your_actual_password")
        print("database = argo_floats")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
