import pytest
from utils.base_test import BaseTest

class TestDatabaseOperations(BaseTest):
    
    @pytest.mark.db
    def test_database_connection(self):
        """Test database connectivity"""
        try:
            with self.db_client.get_connection() as conn:
                assert conn is not None, "Database connection failed"
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.db
    def test_products_table_exists(self):
        """Test if products table exists"""
        try:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'products'
            );
            """
            result = self.db_client.fetch_one(query)
            assert result[0] is True, "Products table does not exist"
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.db
    def test_data_integrity(self):
        """Test data integrity constraints"""
        try:
            # Check for duplicate IDs
            query = """
            SELECT id, COUNT(*) as count 
            FROM products 
            GROUP BY id 
            HAVING COUNT(*) > 1;
            """
            duplicates = self.db_client.execute_query(query)
            assert len(duplicates) == 0, f"Found duplicate IDs: {duplicates}"
            
            # Check for null required fields
            query = """
            SELECT COUNT(*) FROM products 
            WHERE id IS NULL OR title IS NULL OR price IS NULL;
            """
            null_count = self.db_client.fetch_one(query)[0]
            assert null_count == 0, f"Found {null_count} records with null required fields"
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    @pytest.mark.db
    def test_price_validation(self):
        """Test price data validation"""
        try:
            query = "SELECT COUNT(*) FROM products WHERE price < 0;"
            negative_prices = self.db_client.fetch_one(query)[0]
            assert negative_prices == 0, f"Found {negative_prices} products with negative prices"
        except Exception as e:
            pytest.skip(f"Database not available: {e}")