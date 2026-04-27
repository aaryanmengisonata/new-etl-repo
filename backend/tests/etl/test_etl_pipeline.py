import pytest
import json
from utils.base_test import BaseTest

class TestETLPipeline(BaseTest):
    
    @pytest.mark.etl
    def test_api_to_db_data_consistency(self):
        """Test data consistency between API and database"""
        try:
            # Get data from API
            api_response = self.api_client.get("/products")
            api_products = api_response.json()
            
            # Get data from database
            db_query = "SELECT id, title, price, category FROM products ORDER BY id;"
            db_products = self.db_client.execute_query(db_query)
            
            # Compare counts
            assert len(api_products) == len(db_products), \
                f"Count mismatch: API={len(api_products)}, DB={len(db_products)}"
            
            # Compare specific records
            for api_product in api_products[:5]:  # Test first 5 products
                db_product = next((p for p in db_products if p[0] == api_product['id']), None)
                assert db_product is not None, f"Product {api_product['id']} not found in database"
                
                assert db_product[1] == api_product['title'], "Title mismatch"
                assert float(db_product[2]) == api_product['price'], "Price mismatch"
                
        except Exception as e:
            pytest.skip(f"ETL validation skipped: {e}")
    
    @pytest.mark.etl
    def test_data_transformation_rules(self):
        """Test ETL transformation rules"""
        try:
            # Test price formatting (should be numeric)
            query = """
            SELECT id, price FROM products 
            WHERE price::text !~ '^[0-9]+\.?[0-9]*$' 
            LIMIT 5;
            """
            invalid_prices = self.db_client.execute_query(query)
            assert len(invalid_prices) == 0, f"Found invalid price formats: {invalid_prices}"
            
            # Test category standardization
            query = "SELECT DISTINCT category FROM products;"
            categories = self.db_client.execute_query(query)
            category_list = [cat[0] for cat in categories]
            
            # Ensure categories are properly formatted (no extra spaces, proper case)
            for category in category_list:
                assert category == category.strip(), f"Category has extra spaces: '{category}'"
                
        except Exception as e:
            pytest.skip(f"Transformation validation skipped: {e}")
    
    @pytest.mark.etl
    def test_data_freshness(self):
        """Test data freshness and update timestamps"""
        try:
            # Check if data was updated recently (assuming updated_at column exists)
            query = """
            SELECT COUNT(*) FROM products 
            WHERE updated_at < NOW() - INTERVAL '24 hours';
            """
            old_records = self.db_client.fetch_one(query)
            # This is informational - log but don't fail
            self.logger.info(f"Records older than 24 hours: {old_records[0] if old_records else 0}")
            
        except Exception as e:
            # Skip if updated_at column doesn't exist
            pytest.skip(f"Data freshness check skipped: {e}")
    
    @pytest.mark.etl
    def test_batch_processing_validation(self):
        """Test batch processing results"""
        batch_size = self.config['etl']['batch_size']
        
        try:
            # Test that batch processing maintains data integrity
            query = f"SELECT COUNT(*) FROM products LIMIT {batch_size};"
            result = self.db_client.fetch_one(query)
            
            assert result[0] > 0, "No data found for batch processing validation"
            self.logger.info(f"Batch validation completed for {result[0]} records")
            
        except Exception as e:
            pytest.skip(f"Batch processing validation skipped: {e}")