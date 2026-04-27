import sqlite3
import os
from datetime import datetime
import requests
import logging

class DatabaseInitializer:
    def __init__(self, use_sqlite=True):
        self.use_sqlite = use_sqlite
        self.logger = logging.getLogger(__name__)
        
    def init_sqlite(self):
        """Initialize SQLite database"""
        db_path = "etl_test.db"
        
        # Remove existing database
        if os.path.exists(db_path):
            os.remove(db_path)
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE products (
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
        
        cursor.execute('''
            CREATE TABLE etl_logs (
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
        
        # Load data from API
        self.load_api_data_sqlite(cursor)
        
        conn.commit()
        conn.close()
        
        print(f"SQLite database created: {db_path}")
        return db_path
    
    def load_api_data_sqlite(self, cursor):
        """Load data from API into SQLite"""
        try:
            response = requests.get("https://fakestoreapi.com/products", timeout=10, verify=False)
            products = response.json()
            
            for product in products:
                rating = product.get('rating', {})
                cursor.execute('''
                    INSERT INTO products (id, title, price, description, category, image, rating_rate, rating_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product['id'],
                    product['title'],
                    product['price'],
                    product.get('description'),
                    product['category'],
                    product.get('image'),
                    rating.get('rate'),
                    rating.get('count')
                ))
            
            print(f"Loaded {len(products)} products from API")
            
        except Exception as e:
            print(f"Failed to load API data: {e}")
            # Insert sample data
            cursor.execute('''
                INSERT INTO products (id, title, price, category, description)
                VALUES (1, 'Test Product 1', 29.99, 'electronics', 'Sample product')
            ''')

if __name__ == "__main__":
    init = DatabaseInitializer()
    init.init_sqlite()