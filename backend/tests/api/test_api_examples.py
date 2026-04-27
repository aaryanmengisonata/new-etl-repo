import pytest
import allure
import json
from utils.base_test import BaseTest

@allure.epic("ETL Testing Framework")
@allure.feature("API Testing")
class TestAPIExamples(BaseTest):
    """
    API Testing Examples - Learn how to test APIs step by step
    
    This file demonstrates:
    1. Basic API calls (GET, POST, PUT, DELETE)
    2. Response validation (status, headers, data)
    3. JSON schema validation
    4. Error handling
    5. Data validation
    6. Performance testing
    """
    
    @allure.story("Basic API Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_get_all_products_basic(self):
        """Test 1: Basic GET request validation"""
        
        with allure.step("Send GET request to /products endpoint"):
            response = self.api_client.get("/products")
            allure.attach("Request URL", f"{self.api_client.base_url}/products", allure.attachment_type.TEXT)
        
        with allure.step("Validate response status code"):
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            allure.attach("Status Code", str(response.status_code), allure.attachment_type.TEXT)
        
        with allure.step("Validate response is JSON"):
            products = response.json()
            assert isinstance(products, list), "Response should be a list"
            allure.attach("Response Type", str(type(products)), allure.attachment_type.TEXT)
        
        with allure.step("Validate data count"):
            assert len(products) > 0, "Products list should not be empty"
            allure.attach("Products Count", str(len(products)), allure.attachment_type.TEXT)
            allure.attach("Sample Products", json.dumps(products[:2], indent=2), allure.attachment_type.JSON)

    @allure.story("Single Product Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_get_single_product_detailed(self):
        """Test 2: Detailed single product validation"""
        
        product_id = 1
        
        with allure.step(f"Send GET request for product ID {product_id}"):
            response = self.api_client.get(f"/products/{product_id}")
            allure.attach("Request URL", f"{self.api_client.base_url}/products/{product_id}", allure.attachment_type.TEXT)
        
        with allure.step("Validate response status and headers"):
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
            allure.attach("Content-Type", response.headers.get("content-type"), allure.attachment_type.TEXT)
        
        with allure.step("Parse and validate product data"):
            product = response.json()
            allure.attach("Product Data", json.dumps(product, indent=2), allure.attachment_type.JSON)
            
            # Validate required fields
            required_fields = ["id", "title", "price", "category", "description", "image"]
            for field in required_fields:
                assert field in product, f"Required field '{field}' missing"
                assert product[field] is not None, f"Field '{field}' should not be null"
        
        with allure.step("Validate data types"):
            assert isinstance(product["id"], int), "ID should be integer"
            assert isinstance(product["title"], str), "Title should be string"
            assert isinstance(product["price"], (int, float)), "Price should be numeric"
            assert isinstance(product["category"], str), "Category should be string"
            
            allure.attach("Data Types Validation", "All data types are correct", allure.attachment_type.TEXT)
        
        with allure.step("Validate business rules"):
            assert product["id"] == product_id, f"Product ID should match requested ID {product_id}"
            assert product["price"] > 0, "Price should be positive"
            assert len(product["title"]) > 0, "Title should not be empty"
            
            allure.attach("Business Rules", "All business rules passed", allure.attachment_type.TEXT)

    @allure.story("JSON Schema Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_product_schema_validation(self):
        """Test 3: JSON schema validation"""
        
        with allure.step("Get product data"):
            response = self.api_client.get("/products/1")
            product = response.json()
        
        with allure.step("Load JSON schema"):
            with open('schemas/product_schema.json', 'r') as f:
                schema = json.load(f)
            allure.attach("Schema", json.dumps(schema, indent=2), allure.attachment_type.JSON)
        
        with allure.step("Validate product against schema"):
            self.validate_response_schema(product, schema)
            allure.attach("Schema Validation", "Product matches schema", allure.attachment_type.TEXT)

    @allure.story("API Error Handling")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.api
    def test_api_error_handling(self):
        """Test 4: Error handling for invalid requests"""
        
        with allure.step("Test invalid product ID"):
            response = self.api_client.get("/products/99999")
            # Note: Fake Store API returns empty object for invalid ID, not 404
            allure.attach("Invalid ID Response", str(response.status_code), allure.attachment_type.TEXT)
        
        with allure.step("Test invalid endpoint"):
            response = self.api_client.get("/invalid-endpoint")
            assert response.status_code == 404, "Should return 404 for invalid endpoint"
            allure.attach("Invalid Endpoint Status", str(response.status_code), allure.attachment_type.TEXT)

    @allure.story("Categories API Testing")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_categories_endpoint(self):
        """Test 5: Categories endpoint validation"""
        
        with allure.step("Get all categories"):
            response = self.api_client.get("/products/categories")
            assert response.status_code == 200
            categories = response.json()
        
        with allure.step("Validate categories data"):
            assert isinstance(categories, list), "Categories should be a list"
            assert len(categories) > 0, "Should have at least one category"
            
            for category in categories:
                assert isinstance(category, str), "Each category should be a string"
                assert len(category) > 0, "Category name should not be empty"
            
            allure.attach("Categories", json.dumps(categories, indent=2), allure.attachment_type.JSON)
            allure.attach("Categories Count", str(len(categories)), allure.attachment_type.TEXT)

    @allure.story("Products by Category")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_products_by_category(self):
        """Test 6: Filter products by category"""
        
        with allure.step("Get available categories"):
            categories_response = self.api_client.get("/products/categories")
            categories = categories_response.json()
            test_category = categories[0]  # Use first category
            allure.attach("Test Category", test_category, allure.attachment_type.TEXT)
        
        with allure.step(f"Get products for category: {test_category}"):
            response = self.api_client.get(f"/products/category/{test_category}")
            assert response.status_code == 200
            products = response.json()
        
        with allure.step("Validate filtered products"):
            assert isinstance(products, list), "Products should be a list"
            assert len(products) > 0, f"Should have products in category {test_category}"
            
            # Verify all products belong to the requested category
            for product in products:
                assert product["category"] == test_category, f"Product category mismatch"
            
            allure.attach("Filtered Products Count", str(len(products)), allure.attachment_type.TEXT)
            allure.attach("Sample Filtered Products", json.dumps(products[:2], indent=2), allure.attachment_type.JSON)

    @allure.story("API Performance Testing")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.api
    def test_api_performance(self):
        """Test 7: Basic API performance validation"""
        
        import time
        
        with allure.step("Measure API response time"):
            start_time = time.time()
            response = self.api_client.get("/products")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200, "API should respond successfully"
            assert response_time < 5.0, f"API response time {response_time:.2f}s should be under 5 seconds"
            
            allure.attach("Response Time", f"{response_time:.3f} seconds", allure.attachment_type.TEXT)
            allure.attach("Performance Status", "PASSED" if response_time < 2.0 else "SLOW", allure.attachment_type.TEXT)

    @allure.story("Data Consistency Check")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_data_consistency_across_endpoints(self):
        """Test 8: Data consistency between different endpoints"""
        
        with allure.step("Get all products"):
            all_products_response = self.api_client.get("/products")
            all_products = all_products_response.json()
            total_count = len(all_products)
        
        with allure.step("Get individual products and compare"):
            # Test first 3 products for consistency
            for i in range(min(3, total_count)):
                product_id = all_products[i]["id"]
                
                single_product_response = self.api_client.get(f"/products/{product_id}")
                single_product = single_product_response.json()
                
                # Compare data consistency
                assert all_products[i]["id"] == single_product["id"], "ID mismatch"
                assert all_products[i]["title"] == single_product["title"], "Title mismatch"
                assert all_products[i]["price"] == single_product["price"], "Price mismatch"
                
                allure.attach(f"Product {product_id} Consistency", "PASSED", allure.attachment_type.TEXT)
        
        allure.attach("Data Consistency Check", "All products consistent across endpoints", allure.attachment_type.TEXT)