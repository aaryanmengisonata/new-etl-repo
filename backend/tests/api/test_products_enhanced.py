import pytest
import json
from utils.base_test import BaseTest

class TestProductsAPI(BaseTest):
    
    @pytest.mark.api
    def test_get_all_products(self):
        response = self.api_client.get("/products")
        self.validate_response_status(response, 200)
        
        products = response.json()
        assert isinstance(products, list), "Response should be a list"
        assert len(products) > 0, "Products list should not be empty"
    
    @pytest.mark.api
    def test_get_single_product(self):
        response = self.api_client.get("/products/1")
        self.validate_response_status(response, 200)
        
        product = response.json()
        with open('schemas/product_schema.json', 'r') as f:
            schema = json.load(f)
        
        self.validate_response_schema(product, schema)
        self.validate_required_fields(product, ["id", "title", "price", "category"])
    
    @pytest.mark.api
    def test_get_product_categories(self):
        response = self.api_client.get("/products/categories")
        self.validate_response_status(response, 200)
        
        categories = response.json()
        assert isinstance(categories, list), "Categories should be a list"
        assert len(categories) > 0, "Categories should not be empty"
    
    @pytest.mark.api
    def test_products_by_category(self):
        # First get categories
        categories_response = self.api_client.get("/products/categories")
        categories = categories_response.json()
        
        # Test first category
        if categories:
            category = categories[0]
            response = self.api_client.get(f"/products/category/{category}")
            self.validate_response_status(response, 200)
            
            products = response.json()
            assert isinstance(products, list), "Products should be a list"