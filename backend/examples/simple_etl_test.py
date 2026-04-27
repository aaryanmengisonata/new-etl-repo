import sys
import os
sys.path.append(os.getcwd())

from utils.sqlite_client import SQLiteClient
from utils.api_client import APIClient

def test_etl_data_consistency():
    """Simple ETL test: API to Database consistency"""
    
    print("=== ETL Test: API to Database Consistency ===")
    
    # Initialize clients
    db = SQLiteClient()
    api = APIClient("https://fakestoreapi.com")
    
    # Get data from API
    print("1. Fetching data from API...")
    api_response = api.get("/products")
    api_products = api_response.json()
    print(f"   API returned {len(api_products)} products")
    
    # Get data from database
    print("2. Fetching data from database...")
    db_products = db.execute_query("SELECT id, title, price, category FROM products ORDER BY id")
    print(f"   Database has {len(db_products)} products")
    
    # Test 1: Count consistency
    print("3. Testing count consistency...")
    assert len(api_products) == len(db_products), f"Count mismatch: API={len(api_products)}, DB={len(db_products)}"
    print("   [OK] Counts match")
    
    # Test 2: Data consistency (first 3 products)
    print("4. Testing data consistency...")
    for i in range(min(3, len(api_products))):
        api_product = api_products[i]
        db_product = db_products[i]
        
        # Check ID
        assert api_product['id'] == db_product[0], f"ID mismatch: API={api_product['id']}, DB={db_product[0]}"
        
        # Check title
        assert api_product['title'] == db_product[1], f"Title mismatch for ID {api_product['id']}"
        
        # Check price
        assert api_product['price'] == db_product[2], f"Price mismatch for ID {api_product['id']}"
        
        print(f"   [OK] Product {api_product['id']}: {api_product['title']} - ${api_product['price']}")
    
    # Test 3: Data quality checks
    print("5. Testing data quality...")
    
    # Check for negative prices
    negative_prices = db.execute_query("SELECT COUNT(*) FROM products WHERE price < 0")[0][0]
    assert negative_prices == 0, f"Found {negative_prices} products with negative prices"
    print("   [OK] No negative prices")
    
    # Check for empty titles
    empty_titles = db.execute_query("SELECT COUNT(*) FROM products WHERE title IS NULL OR title = ''")[0][0]
    assert empty_titles == 0, f"Found {empty_titles} products with empty titles"
    print("   [OK] No empty titles")
    
    # Check categories
    categories = db.execute_query("SELECT DISTINCT category FROM products")
    category_count = len(categories)
    print(f"   [OK] Found {category_count} unique categories")
    
    print("\n[SUCCESS] ETL Test PASSED! Data consistency verified.")
    return True

if __name__ == "__main__":
    test_etl_data_consistency()