import snowflake.connector
import logging
from contextlib import contextmanager
import configparser
import os

class SnowflakeClient:
    def __init__(self, config_file="config/master.properties"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_file)
        self.connection_params = self._get_connection_params()
    
    def _load_config(self, config_file):
        """Load configuration from properties file"""
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file)
        return config
    
    def _get_connection_params(self):
        """Get Snowflake connection parameters"""
        return {
            'account': self.config.get('DATABASE', 'SNOWFLAKE_ACCOUNT', fallback=''),
            'user': self.config.get('DATABASE', 'SNOWFLAKE_USER', fallback=''),
            'password': self.config.get('DATABASE', 'SNOWFLAKE_PASSWORD', fallback=''),
            'warehouse': self.config.get('DATABASE', 'SNOWFLAKE_WAREHOUSE', fallback=''),
            'database': self.config.get('DATABASE', 'SNOWFLAKE_DATABASE', fallback=''),
            'schema': self.config.get('DATABASE', 'SNOWFLAKE_SCHEMA', fallback='')
        }
    
    @contextmanager
    def get_connection(self):
        """Get Snowflake connection"""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            yield conn
        except Exception as e:
            self.logger.error(f"Snowflake connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute query on Snowflake"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            query_upper = query.strip().upper()
            if query_upper.startswith('SELECT') or query_upper.startswith('SHOW') or query_upper.startswith('DESCRIBE'):
                return cursor.fetchall()
            
            return cursor.rowcount
    
    def fetch_one(self, query: str, params: tuple = None):
        """Fetch single result from Snowflake"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
    
    def test_connection(self):
        """Test Snowflake connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False