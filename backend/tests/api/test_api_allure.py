import pytest
import allure
import json
from utils.base_test import BaseTest

@allure.epic("ETL Testing Framework")
@allure.feature("API Testing")
class TestAPIAllure(BaseTest):
    
    @allure.story("Product API Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_get_all_products_allure(self):
        """Test API products endpoint with Allure reporting"""
        
        with allure.step("Send GET request to /products"):
            response = self.api_client.get("/products")
            allure.attach("Request URL", f"{self.api_client.base_url}/products", allure.attachment_type.TEXT)
        
        with allure.step("Validate response status"):
            allure.attach("Response Status", str(response.status_code), allure.attachment_type.TEXT)
            self.validate_response_status(response, 200)
        
        with allure.step("Validate response data"):
            products = response.json()
            allure.attach("Products Count", str(len(products)), allure.attachment_type.TEXT)
            allure.attach("Sample Products", json.dumps(products[:2], indent=2), allure.attachment_type.JSON)
            
            assert isinstance(products, list), "Response should be a list"
            assert len(products) > 0, "Products list should not be empty"
    
    @allure.story("Single Product Validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_get_single_product_allure(self):
        """Test single product API endpoint"""
        
        with allure.step("Send GET request to /products/1"):
            response = self.api_client.get("/products/1")
            allure.attach("Request URL", f"{self.api_client.base_url}/products/1", allure.attachment_type.TEXT)
        
        with allure.step("Validate response"):
            self.validate_response_status(response, 200)
            product = response.json()
            
            allure.attach("Product Data", json.dumps(product, indent=2), allure.attachment_type.JSON)
        
        with allure.step("Validate required fields"):
            required_fields = ["id", "title", "price", "category"]
            self.validate_required_fields(product, required_fields)
            
            for field in required_fields:
                allure.attach(f"Field: {field}", str(product.get(field)), allure.attachment_type.TEXT)
    
    @allure.story("Categories API Validation")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.api
    def test_get_categories_allure(self):
        """Test categories API endpoint"""
        
        with allure.step("Send GET request to /products/categories"):
            response = self.api_client.get("/products/categories")
        
        with allure.step("Validate categories response"):
            self.validate_response_status(response, 200)
            categories = response.json()
            
            allure.attach("Categories", json.dumps(categories, indent=2), allure.attachment_type.JSON)
            allure.attach("Categories Count", str(len(categories)), allure.attachment_type.TEXT)
            
            assert isinstance(categories, list), "Categories should be a list"
            assert len(categories) > 0, "Categories should not be empty"