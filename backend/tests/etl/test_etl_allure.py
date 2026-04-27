import pytest
import allure
import json
from utils.base_test import BaseTest

@allure.epic("ETL Testing Framework")
@allure.feature("Data Pipeline Validation")
class TestETLPipelineAllure(BaseTest):
    
    @allure.story("API to Database Consistency")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.etl
    def test_api_to_db_data_consistency(self):
        """Test data consistency between API and database with Allure reporting"""
        
        with allure.step("Initialize API and Database clients"):
            # Clients already initialized in BaseTest
            allure.attach("API Base URL", self.api_client.base_url, allure.attachment_type.TEXT)
        
        with allure.step("Fetch data from API"):
            api_response = self.api_client.get("/products")
            api_products = api_response.json()
            
            allure.attach("API Response Status", str(api_response.status_code), allure.attachment_type.TEXT)
            allure.attach("API Products Count", str(len(api_products)), allure.attachment_type.TEXT)
            allure.attach("Sample API Data", json.dumps(api_products[:2], indent=2), allure.attachment_type.JSON)
        
        with allure.step("Fetch data from database"):
            db_query = "SELECT id, title, price, category FROM products ORDER BY id"
            db_products = self.db_client.execute_query(db_query)
            
            allure.attach("Database Query", db_query, allure.attachment_type.TEXT)
            allure.attach("Database Products Count", str(len(db_products)), allure.attachment_type.TEXT)
        
        with allure.step("Validate data count consistency"):
            assert len(api_products) == len(db_products), \
                f"Count mismatch: API={len(api_products)}, DB={len(db_products)}"
            allure.attach("Count Validation", f"API: {len(api_products)}, DB: {len(db_products)} - MATCH", allure.attachment_type.TEXT)
        
        with allure.step("Validate individual record consistency"):
            mismatches = []
            for i in range(min(5, len(api_products))):
                api_product = api_products[i]
                db_product = next((p for p in db_products if p[0] == api_product['id']), None)
                
                if db_product is None:
                    mismatches.append(f"Product {api_product['id']} not found in database")
                    continue
                
                if db_product[1] != api_product['title']:
                    mismatches.append(f"Title mismatch for ID {api_product['id']}")
                
                if float(db_product[2]) != api_product['price']:
                    mismatches.append(f"Price mismatch for ID {api_product['id']}")
            
            if mismatches:
                allure.attach("Data Mismatches", "\n".join(mismatches), allure.attachment_type.TEXT)
                pytest.fail(f"Found {len(mismatches)} data mismatches")
            else:
                allure.attach("Data Validation", "All records match between API and Database", allure.attachment_type.TEXT)
    
    @allure.story("Data Quality Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.etl
    def test_data_quality_checks(self):
        """Test data quality rules and constraints"""
        
        with allure.step("Check for negative prices"):
            negative_prices = self.db_client.execute_query("SELECT COUNT(*) FROM products WHERE price < 0")[0][0]
            allure.attach("Negative Prices Count", str(negative_prices), allure.attachment_type.TEXT)
            assert negative_prices == 0, f"Found {negative_prices} products with negative prices"
        
        with allure.step("Check for empty titles"):
            empty_titles = self.db_client.execute_query("SELECT COUNT(*) FROM products WHERE title IS NULL OR title = ''")[0][0]
            allure.attach("Empty Titles Count", str(empty_titles), allure.attachment_type.TEXT)
            assert empty_titles == 0, f"Found {empty_titles} products with empty titles"
        
        with allure.step("Validate categories"):
            categories = self.db_client.execute_query("SELECT DISTINCT category FROM products")
            category_list = [cat[0] for cat in categories]
            
            allure.attach("Categories Found", json.dumps(category_list, indent=2), allure.attachment_type.JSON)
            allure.attach("Category Count", str(len(category_list)), allure.attachment_type.TEXT)
            
            # Check for proper formatting
            for category in category_list:
                assert category == category.strip(), f"Category has extra spaces: '{category}'"
                assert len(category) > 0, "Found empty category"
    
    @allure.story("ETL Performance Metrics")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.etl
    def test_etl_performance_metrics(self):
        """Test ETL performance and record processing"""
        
        with allure.step("Measure database query performance"):
            import time
            start_time = time.time()
            
            products = self.db_client.execute_query("SELECT * FROM products")
            
            query_time = time.time() - start_time
            allure.attach("Query Execution Time", f"{query_time:.3f} seconds", allure.attachment_type.TEXT)
            allure.attach("Records Retrieved", str(len(products)), allure.attachment_type.TEXT)
            
            # Performance assertion (should be fast for test data)
            assert query_time < 1.0, f"Query took too long: {query_time:.3f} seconds"
        
        with allure.step("Check ETL logs table"):
            log_count = self.db_client.execute_query("SELECT COUNT(*) FROM etl_logs")[0][0]
            allure.attach("ETL Log Entries", str(log_count), allure.attachment_type.TEXT)
            
            # ETL logs table should exist and be accessible
            assert log_count >= 0, "ETL logs table not accessible"