import psycopg2
import configparser
from pathlib import Path

def load_config(filename='database.ini', section='database'):
    """Load database configuration from ini file"""
    parser = configparser.ConfigParser()
    parser.read(filename)

    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')

    return config

def get_connection(config_section='database'):
    """Get database connection using configuration"""
    try:
        config = load_config(section=config_section)
        conn = psycopg2.connect(**config)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

class ArgoFloatDB:
    """Simple database connection wrapper for Argo float data"""

    def __init__(self, config_section='database'):
        self.config = load_config(section=config_section)
        self.connection = None

    def connect(self):
        """Establish database connection"""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(**self.config)
        return self.connection

    def execute_query(self, query, params=None, fetch=False):
        """Execute a query with optional parameters"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Query execution failed: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Example usage:
if __name__ == "__main__":
    # Test connection
    with ArgoFloatDB() as db:
        result = db.execute_query("SELECT version();", fetch=True)
        print("Database version:", result[0][0])