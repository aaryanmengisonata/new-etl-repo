import pytest
import allure
import json
from utils.base_test import BaseTest

@allure.epic("ETL Testing Framework")
@allure.feature("Database Testing")
class TestDatabaseExamples(BaseTest):
    """
    Database Testing Examples - Learn how to test databases step by step
    
    This file demonstrates:
    1. Database connectivity testing
    2. Data integrity validation
    3. Schema validation
    4. Data quality checks
    5. Performance testing
    6. Constraint validation
    """
    
    @allure.story("Database Connectivity")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.db
    def test_database_connection(self):
        """Test 1: Basic database connectivity"""
        
        with allure.step("Test database connection"):
            # Simple query to test connection
            result = self.db_client.execute_query("SELECT 1 as test_connection")
            assert result is not None, "Database connection failed"
            allure.attach("Connection Test", "SUCCESS", allure.attachment_type.TEXT)
        
        with allure.step("Verify database file exists"):
            import os
            db_exists = os.path.exists("etl_test.db")
            assert db_exists, "Database file should exist"
            allure.attach("Database File", "etl_test.db exists", allure.attachment_type.TEXT)

    @allure.story("Table Structure Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.db
    def test_table_structure(self):
        """Test 2: Validate table structure and schema"""
        
        with allure.step("Check if required tables exist"):
            # Get all tables
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = self.db_client.execute_query(tables_query)
            table_names = [table[0] for table in tables]
            
            required_tables = ["products", "etl_logs"]
            for table in required_tables:
                assert table in table_names, f"Required table '{table}' not found"
            
            allure.attach("Tables Found", json.dumps(table_names, indent=2), allure.attachment_type.JSON)
        
        with allure.step("Validate products table structure"):
            # Get products table structure
            structure_query = "PRAGMA table_info(products)"
            columns = self.db_client.execute_query(structure_query)
            
            column_names = [col[1] for col in columns]
            required_columns = ["id", "title", "price", "category"]
            
            for column in required_columns:
                assert column in column_names, f"Required column '{column}' not found in products table"
            
            allure.attach("Products Table Columns", json.dumps(column_names, indent=2), allure.attachment_type.JSON)

    @allure.story("Data Integrity Checks")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.db
    def test_data_integrity(self):
        """Test 3: Data integrity validation"""
        
        with allure.step("Check for duplicate IDs"):
            duplicate_query = """
            SELECT id, COUNT(*) as count 
            FROM products 
            GROUP BY id 
            HAVING COUNT(*) > 1
            """
            duplicates = self.db_client.execute_query(duplicate_query)
            assert len(duplicates) == 0, f"Found duplicate IDs: {duplicates}"
            allure.attach("Duplicate Check", "No duplicates found", allure.attachment_type.TEXT)
        
        with allure.step("Check for NULL values in required fields"):
            null_check_query = """
            SELECT COUNT(*) FROM products 
            WHERE id IS NULL OR title IS NULL OR price IS NULL OR category IS NULL
            """
            null_count = self.db_client.fetch_one(null_check_query)[0]
            assert null_count == 0, f"Found {null_count} records with NULL required fields"
            allure.attach("NULL Check", f"Found {null_count} NULL values", allure.attachment_type.TEXT)
        
        with allure.step("Validate primary key constraints"):
            # Check if all IDs are unique and not null
            id_check_query = "SELECT COUNT(DISTINCT id) as unique_ids, COUNT(*) as total_records FROM products"
            result = self.db_client.fetch_one(id_check_query)
            unique_ids, total_records = result[0], result[1]
            
            assert unique_ids == total_records, f"Primary key violation: {unique_ids} unique IDs vs {total_records} total records"
            allure.attach("Primary Key Check", f"Unique IDs: {unique_ids}, Total: {total_records}", allure.attachment_type.TEXT)

    @allure.story("Data Quality Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.db
    def test_data_quality(self):
        """Test 4: Data quality checks"""
        
        with allure.step("Check for negative prices"):
            negative_price_query = "SELECT COUNT(*) FROM products WHERE price < 0"
            negative_count = self.db_client.fetch_one(negative_price_query)[0]
            assert negative_count == 0, f"Found {negative_count} products with negative prices"
            allure.attach("Negative Prices", f"Count: {negative_count}", allure.attachment_type.TEXT)
        
        with allure.step("Check for empty titles"):
            empty_title_query = "SELECT COUNT(*) FROM products WHERE title = '' OR title IS NULL"
            empty_count = self.db_client.fetch_one(empty_title_query)[0]
            assert empty_count == 0, f"Found {empty_count} products with empty titles"
            allure.attach("Empty Titles", f"Count: {empty_count}", allure.attachment_type.TEXT)
        
        with allure.step("Validate price ranges"):
            price_range_query = "SELECT MIN(price) as min_price, MAX(price) as max_price, AVG(price) as avg_price FROM products"
            price_stats = self.db_client.fetch_one(price_range_query)
            min_price, max_price, avg_price = price_stats[0], price_stats[1], price_stats[2]
            
            assert min_price > 0, f"Minimum price should be positive, got {min_price}"
            assert max_price < 10000, f"Maximum price seems unrealistic: {max_price}"
            
            allure.attach("Price Statistics", f"Min: ${min_price}, Max: ${max_price}, Avg: ${avg_price:.2f}", allure.attachment_type.TEXT)
        
        with allure.step("Check category consistency"):
            category_query = "SELECT DISTINCT category FROM products"
            categories = self.db_client.execute_query(category_query)
            category_list = [cat[0] for cat in categories]
            
            # Check for proper formatting
            for category in category_list:
                assert len(category) > 0, "Category should not be empty"
                assert category == category.strip(), f"Category has extra spaces: '{category}'"
            
            allure.attach("Categories", json.dumps(category_list, indent=2), allure.attachment_type.JSON)

    @allure.story("Data Type Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.db
    def test_data_types(self):
        """Test 5: Data type validation"""
        
        with allure.step("Validate numeric fields"):
            # Check if price is numeric
            numeric_check_query = """
            SELECT id, price FROM products 
            WHERE typeof(price) != 'real' AND typeof(price) != 'integer'
            LIMIT 5
            """
            invalid_prices = self.db_client.execute_query(numeric_check_query)
            assert len(invalid_prices) == 0, f"Found non-numeric prices: {invalid_prices}"
            allure.attach("Numeric Validation", "All prices are numeric", allure.attachment_type.TEXT)
        
        with allure.step("Validate string fields"):
            # Check title field types
            string_check_query = """
            SELECT id, title FROM products 
            WHERE typeof(title) != 'text'
            LIMIT 5
            """
            invalid_titles = self.db_client.execute_query(string_check_query)
            assert len(invalid_titles) == 0, f"Found non-text titles: {invalid_titles}"
            allure.attach("String Validation", "All titles are text", allure.attachment_type.TEXT)

    @allure.story("Database Performance")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.db
    def test_database_performance(self):
        """Test 6: Database performance validation"""
        
        import time
        
        with allure.step("Measure query performance"):
            start_time = time.time()
            
            # Execute a complex query
            performance_query = """
            SELECT category, COUNT(*) as product_count, AVG(price) as avg_price
            FROM products 
            GROUP BY category 
            ORDER BY product_count DESC
            """
            results = self.db_client.execute_query(performance_query)
            
            end_time = time.time()
            query_time = end_time - start_time
            
            assert query_time < 1.0, f"Query took too long: {query_time:.3f} seconds"
            assert len(results) > 0, "Query should return results"
            
            allure.attach("Query Time", f"{query_time:.3f} seconds", allure.attachment_type.TEXT)
            allure.attach("Query Results", json.dumps([list(row) for row in results], indent=2), allure.attachment_type.JSON)

    @allure.story("Record Count Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.db
    def test_record_counts(self):
        """Test 7: Record count validation"""
        
        with allure.step("Count total products"):
            count_query = "SELECT COUNT(*) FROM products"
            total_count = self.db_client.fetch_one(count_query)[0]
            
            assert total_count > 0, "Database should have products"
            assert total_count <= 1000, f"Unexpected high count: {total_count}"
            
            allure.attach("Total Products", str(total_count), allure.attachment_type.TEXT)
        
        with allure.step("Count products by category"):
            category_count_query = """
            SELECT category, COUNT(*) as count 
            FROM products 
            GROUP BY category 
            ORDER BY count DESC
            """
            category_counts = self.db_client.execute_query(category_count_query)
            
            for category, count in category_counts:
                assert count > 0, f"Category '{category}' should have products"
            
            allure.attach("Category Counts", json.dumps([list(row) for row in category_counts], indent=2), allure.attachment_type.JSON)

    @allure.story("ETL Log Table Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.db
    def test_etl_logs_table(self):
        """Test 8: ETL logs table validation"""
        
        with allure.step("Verify ETL logs table structure"):
            etl_structure_query = "PRAGMA table_info(etl_logs)"
            etl_columns = self.db_client.execute_query(etl_structure_query)
            etl_column_names = [col[1] for col in etl_columns]
            
            required_etl_columns = ["id", "source_name", "records_processed", "status"]
            for column in required_etl_columns:
                assert column in etl_column_names, f"ETL logs missing column: {column}"
            
            allure.attach("ETL Logs Columns", json.dumps(etl_column_names, indent=2), allure.attachment_type.JSON)
        
        with allure.step("Check ETL logs accessibility"):
            # Just verify we can query the table
            etl_count_query = "SELECT COUNT(*) FROM etl_logs"
            etl_count = self.db_client.fetch_one(etl_count_query)[0]
            
            # ETL logs might be empty, that's okay
            allure.attach("ETL Logs Count", str(etl_count), allure.attachment_type.TEXT)

    @allure.story("Data Consistency Checks")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.db
    def test_data_consistency(self):
        """Test 9: Cross-field data consistency"""
        
        with allure.step("Validate ID sequence"):
            # Check if IDs are in reasonable range
            id_range_query = "SELECT MIN(id) as min_id, MAX(id) as max_id FROM products"
            id_range = self.db_client.fetch_one(id_range_query)
            min_id, max_id = id_range[0], id_range[1]
            
            assert min_id > 0, f"Minimum ID should be positive: {min_id}"
            assert max_id < 10000, f"Maximum ID seems too high: {max_id}"
            
            allure.attach("ID Range", f"Min: {min_id}, Max: {max_id}", allure.attachment_type.TEXT)
        
        with allure.step("Check price-category consistency"):
            # Find any unusual price patterns by category
            price_category_query = """
            SELECT category, MIN(price) as min_price, MAX(price) as max_price, COUNT(*) as count
            FROM products 
            GROUP BY category
            """
            price_patterns = self.db_client.execute_query(price_category_query)
            
            for category, min_price, max_price, count in price_patterns:
                assert min_price <= max_price, f"Price range error in {category}: min={min_price}, max={max_price}"
                assert count > 0, f"Category {category} should have products"
            
            allure.attach("Price Patterns", json.dumps([list(row) for row in price_patterns], indent=2), allure.attachment_type.JSON)