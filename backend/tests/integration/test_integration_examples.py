import pytest
import allure
import json
import time
from utils.base_test import BaseTest

@allure.epic("ETL Testing Framework")
@allure.feature("Integration Testing")
class TestIntegrationExamples(BaseTest):
    """
    Integration Testing Examples - End-to-end system validation
    
    This file demonstrates:
    1. API to Database integration
    2. End-to-end data flow validation
    3. System connectivity testing
    4. Cross-component validation
    5. Performance integration testing
    """
    
    @allure.story("API-Database Integration")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.integration
    def test_api_to_database_sync(self):
        """Test 1: Complete API to Database synchronization"""
        
        with allure.step("Fetch data from API"):
            api_response = self.api_client.get("/products")
            assert api_response.status_code == 200, "API should be accessible"
            api_products = api_response.json()
            assert len(api_products) > 0, "API should return products"
            allure.attach("API Products Count", str(len(api_products)), allure.attachment_type.TEXT)
        
        with allure.step("Verify data exists in database"):
            db_products = self.db_client.execute_query("SELECT * FROM products")
            assert len(db_products) > 0, "Database should have products"
            allure.attach("DB Products Count", str(len(db_products)), allure.attachment_type.TEXT)
        
        with allure.step("Validate data consistency"):
            assert len(api_products) == len(db_products), f"Count mismatch: API={len(api_products)}, DB={len(db_products)}"
            
            # Check specific product data
            api_ids = {product['id'] for product in api_products}
            db_ids = {row[0] for row in db_products}
            assert api_ids == db_ids, "Product IDs should match between API and DB"
            
            allure.attach("Data Sync Status", "SUCCESS - API and DB are synchronized", allure.attachment_type.TEXT)

    @allure.story("End-to-End Data Flow")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.integration
    def test_end_to_end_data_flow(self):
        """Test 2: Complete data flow from source to target"""
        
        with allure.step("Validate source system (API)"):
            products_response = self.api_client.get("/products")
            categories_response = self.api_client.get("/products/categories")
            
            assert products_response.status_code == 200, "Products API should work"
            assert categories_response.status_code == 200, "Categories API should work"
            
            products = products_response.json()
            categories = categories_response.json()
            
            allure.attach("Source Products", str(len(products)), allure.attachment_type.TEXT)
            allure.attach("Source Categories", str(len(categories)), allure.attachment_type.TEXT)
        
        with allure.step("Validate target system (Database)"):
            db_products = self.db_client.execute_query("SELECT COUNT(*) FROM products")
            db_categories = self.db_client.execute_query("SELECT COUNT(DISTINCT category) FROM products")
            
            product_count = db_products[0][0]
            category_count = db_categories[0][0]
            
            assert product_count > 0, "Target should have products"
            assert category_count > 0, "Target should have categories"
            
            allure.attach("Target Products", str(product_count), allure.attachment_type.TEXT)
            allure.attach("Target Categories", str(category_count), allure.attachment_type.TEXT)
        
        with allure.step("Validate data transformation"):
            # Check if data transformations are applied correctly
            price_validation = self.db_client.execute_query(
                "SELECT COUNT(*) FROM products WHERE price > 0 AND price < 10000"
            )
            valid_prices = price_validation[0][0]
            
            title_validation = self.db_client.execute_query(
                "SELECT COUNT(*) FROM products WHERE title IS NOT NULL AND LENGTH(title) > 0"
            )
            valid_titles = title_validation[0][0]
            
            assert valid_prices == product_count, "All prices should be valid"
            assert valid_titles == product_count, "All titles should be valid"
            
            allure.attach("Transformation Status", "SUCCESS - Data properly transformed", allure.attachment_type.TEXT)

    @allure.story("System Connectivity")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.integration
    def test_system_connectivity(self):
        """Test 3: All system components connectivity"""
        
        with allure.step("Test API connectivity"):
            health_check = self.api_client.get("/products/1")
            assert health_check.status_code == 200, "API should be reachable"
            allure.attach("API Status", "CONNECTED", allure.attachment_type.TEXT)
        
        with allure.step("Test Database connectivity"):
            db_check = self.db_client.execute_query("SELECT 1")
            assert db_check is not None, "Database should be reachable"
            allure.attach("Database Status", "CONNECTED", allure.attachment_type.TEXT)
        
        with allure.step("Test cross-system data access"):
            # Verify we can access data from both systems simultaneously
            api_product = self.api_client.get("/products/1").json()
            db_product = self.db_client.fetch_one("SELECT * FROM products WHERE id = 1")
            
            assert api_product['id'] == db_product[0], "Cross-system data should match"
            allure.attach("Cross-System Check", "SUCCESS", allure.attachment_type.TEXT)

    @allure.story("Data Quality Integration")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.integration
    def test_data_quality_integration(self):
        """Test 4: Data quality across systems"""
        
        with allure.step("Compare data quality metrics"):
            # API data quality
            api_products = self.api_client.get("/products").json()
            api_complete_products = [p for p in api_products if p.get('title') and p.get('price') and p.get('category')]
            
            # Database data quality
            db_complete = self.db_client.execute_query(
                "SELECT COUNT(*) FROM products WHERE title IS NOT NULL AND price > 0 AND category IS NOT NULL"
            )
            db_complete_count = db_complete[0][0]
            
            assert len(api_complete_products) == db_complete_count, "Data quality should be consistent"
            
            allure.attach("API Complete Records", str(len(api_complete_products)), allure.attachment_type.TEXT)
            allure.attach("DB Complete Records", str(db_complete_count), allure.attachment_type.TEXT)
        
        with allure.step("Validate business rules across systems"):
            # Check price ranges
            api_prices = [p['price'] for p in api_products if p.get('price')]
            db_prices = self.db_client.execute_query("SELECT price FROM products WHERE price IS NOT NULL")
            db_price_values = [row[0] for row in db_prices]
            
            api_avg_price = sum(api_prices) / len(api_prices)
            db_avg_price = sum(db_price_values) / len(db_price_values)
            
            price_diff = abs(api_avg_price - db_avg_price)
            assert price_diff < 0.01, f"Average price difference too high: {price_diff}"
            
            allure.attach("Price Consistency", f"API: ${api_avg_price:.2f}, DB: ${db_avg_price:.2f}", allure.attachment_type.TEXT)

    @allure.story("Performance Integration")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.integration
    def test_performance_integration(self):
        """Test 5: End-to-end performance validation"""
        
        with allure.step("Measure API response time"):
            start_time = time.time()
            api_response = self.api_client.get("/products")
            api_time = time.time() - start_time
            
            assert api_response.status_code == 200, "API should respond successfully"
            assert api_time < 5.0, f"API response too slow: {api_time:.2f}s"
            
            allure.attach("API Response Time", f"{api_time:.3f} seconds", allure.attachment_type.TEXT)
        
        with allure.step("Measure database query time"):
            start_time = time.time()
            db_result = self.db_client.execute_query("SELECT * FROM products")
            db_time = time.time() - start_time
            
            assert len(db_result) > 0, "Database should return results"
            assert db_time < 1.0, f"Database query too slow: {db_time:.2f}s"
            
            allure.attach("DB Query Time", f"{db_time:.3f} seconds", allure.attachment_type.TEXT)
        
        with allure.step("Measure end-to-end processing time"):
            start_time = time.time()
            
            # Simulate complete ETL process
            api_data = self.api_client.get("/products").json()
            db_count = self.db_client.execute_query("SELECT COUNT(*) FROM products")[0][0]
            validation_result = len(api_data) == db_count
            
            total_time = time.time() - start_time
            
            assert validation_result, "End-to-end validation should pass"
            assert total_time < 10.0, f"End-to-end process too slow: {total_time:.2f}s"
            
            allure.attach("End-to-End Time", f"{total_time:.3f} seconds", allure.attachment_type.TEXT)

    @allure.story("Error Handling Integration")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.integration
    def test_error_handling_integration(self):
        """Test 6: Error handling across systems"""
        
        with allure.step("Test API error handling"):
            # Test invalid endpoint
            error_response = self.api_client.get("/products/99999")
            assert error_response.status_code == 404, "API should handle invalid requests"
            allure.attach("API Error Handling", "SUCCESS - 404 for invalid product", allure.attachment_type.TEXT)
        
        with allure.step("Test database error handling"):
            # Test invalid query handling
            try:
                self.db_client.execute_query("SELECT * FROM non_existent_table")
                assert False, "Should raise exception for invalid table"
            except Exception as e:
                assert "no such table" in str(e).lower(), "Should get proper error message"
                allure.attach("DB Error Handling", "SUCCESS - Proper error for invalid table", allure.attachment_type.TEXT)
        
        with allure.step("Test graceful degradation"):
            # Verify system can handle partial failures
            db_products = self.db_client.execute_query("SELECT COUNT(*) FROM products")
            product_count = db_products[0][0]
            
            assert product_count > 0, "System should maintain data integrity during errors"
            allure.attach("Graceful Degradation", "SUCCESS - Data integrity maintained", allure.attachment_type.TEXT)

    @allure.story("Configuration Integration")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.integration
    def test_configuration_integration(self):
        """Test 7: Configuration and environment integration"""
        
        with allure.step("Validate environment configuration"):
            import os
            
            # Check if database file exists
            db_exists = os.path.exists("etl_test.db")
            assert db_exists, "Database file should exist"
            
            # Check database size (should have data)
            db_size = os.path.getsize("etl_test.db")
            assert db_size > 1000, f"Database should have substantial data: {db_size} bytes"
            
            allure.attach("Environment Check", f"DB exists: {db_exists}, Size: {db_size} bytes", allure.attachment_type.TEXT)
        
        with allure.step("Validate API configuration"):
            # Test API base URL configuration
            response = self.api_client.get("/products/categories")
            assert response.status_code == 200, "API configuration should be correct"
            
            categories = response.json()
            assert len(categories) > 0, "API should return valid data"
            
            allure.attach("API Configuration", f"Categories available: {len(categories)}", allure.attachment_type.TEXT)