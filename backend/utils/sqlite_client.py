import sqlite3
import logging
import os
from contextlib import contextmanager
from datetime import datetime

class SQLiteClient:
    def __init__(self, db_path="etl_test.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    image TEXT,
                    rating_rate REAL,
                    rating_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ETL logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS etl_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    records_processed INTEGER,
                    records_success INTEGER,
                    records_failed INTEGER,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'RUNNING'
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            query_upper = query.strip().upper()
            if query_upper.startswith('SELECT') or query_upper.startswith('PRAGMA'):
                return cursor.fetchall()
            conn.commit()
            return cursor.rowcount
    
    def fetch_one(self, query: str, params: tuple = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()