import sys
import os
sys.path.append(os.getcwd())

from utils.sqlite_client import SQLiteClient

# Test database connection
db = SQLiteClient()

# Test query
result = db.execute_query("SELECT COUNT(*) FROM products")
print(f"Products count: {result[0][0]}")

# Test specific product
product = db.fetch_one("SELECT id, title, price FROM products WHERE id = 1")
print(f"Product 1: {product}")

print("Database connection successful!")