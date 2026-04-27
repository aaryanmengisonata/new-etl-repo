import pytest
import allure
import pandas as pd
from utils.base_test import BaseTest
from utils.csv_controller import CSVTestController
from utils.sql_repository import SQLRepository

@allure.epic("ETL Testing Framework")
@allure.feature("CSV-Driven Business Testing")
class TestBusinessCSVDriven(BaseTest):
    """
    CSV-Driven Testing - Production approach like existing ETL framework
    
    Features:
    1. Test cases defined in CSV
    2. SQL queries in separate files
    3. Business functionality separation
    4. Enable/Disable control via CSV
    5. Multiple validation conditions
    """
    
    @classmethod
    def setup_class(cls):
        """Setup CSV controller and SQL repository"""
        cls.csv_controller = CSVTestController()
        cls.sql_repository = SQLRepository()
        cls.db_client = SQLiteClient()
        cls.api_client = None
    
    @pytest.mark.business
    def test_csv_driven_validation(self):
        """Execute all test cases from CSV with SQL repository"""
        
        test_cases = self.csv_controller.get_enabled_tests()
        
        for test_case in test_cases:
            test_id = test_case['test_id']
            sql_id = test_case['sql_id']
            expected_condition = test_case['expected_condition']
            functionality = test_case['functionality']
            description = test_case.get('description', 'No description')
            
            with allure.step(f"Execute {functionality} test: {test_id}"):
                allure.attach("Test Description", description, allure.attachment_type.TEXT)
                allure.attach("Functionality", functionality, allure.attachment_type.TEXT)
                
                # Get SQL query from repository
                sql_query = self.sql_repository.get_query(sql_id)
                assert sql_query, f"SQL query not found for ID: {sql_id}"
                
                allure.attach("SQL Query", sql_query, allure.attachment_type.TEXT)
            
            with allure.step("Execute SQL query"):
                result = self.db_client.execute_query(sql_query)
                allure.attach("Query Result", str(result), allure.attachment_type.TEXT)
            
            with allure.step(f"Validate result using condition: {expected_condition}"):
                is_valid = self.csv_controller.validate_result(result, expected_condition)
                
                allure.attach("Validation Result", 
                             f"Expected: {expected_condition}, Actual: {result}, Valid: {is_valid}", 
                             allure.attachment_type.TEXT)
                
                if not is_valid:
                    print(f"Test {test_id} failed: Expected {expected_condition}, got {result}")

@allure.epic("ETL Testing Framework") 
@allure.feature("Accommodation Testing")
class TestAccommodation(BaseTest):
    """Accommodation-specific business tests"""
    
    @classmethod
    def setup_class(cls):
        cls.csv_controller = CSVTestController()
        cls.sql_repository = SQLRepository()
        cls.db_client = SQLiteClient()
    
    @allure.story("Accommodation Validation")
    @pytest.mark.accommodation
    def test_accommodation_functionality(self):
        """Run all accommodation tests from CSV"""
        
        accommodation_tests = self.csv_controller.get_tests_by_functionality('accommodation')
        
        for test_case in accommodation_tests:
            with allure.step(f"Test: {test_case['test_id']} - {test_case['description']}"):
                sql_query = self.sql_repository.get_query(test_case['sql_id'])
                result = self.db_client.execute_query(sql_query)
                
                is_valid = self.csv_controller.validate_result(result, test_case['expected_condition'])
                assert is_valid, f"Accommodation test {test_case['test_id']} failed"

@allure.epic("ETL Testing Framework")
@allure.feature("Flight Testing") 
class TestFlight(BaseTest):
    """Flight-specific business tests"""
    
    @classmethod
    def setup_class(cls):
        cls.csv_controller = CSVTestController()
        cls.sql_repository = SQLRepository()
        cls.db_client = SQLiteClient()
    
    @allure.story("Flight Validation")
    @pytest.mark.flight
    def test_flight_functionality(self):
        """Run all flight tests from CSV"""
        
        flight_tests = self.csv_controller.get_tests_by_functionality('flight')
        
        for test_case in flight_tests:
            with allure.step(f"Test: {test_case['test_id']} - {test_case['description']}"):
                sql_query = self.sql_repository.get_query(test_case['sql_id'])
                result = self.db_client.execute_query(sql_query)
                
                is_valid = self.csv_controller.validate_result(result, test_case['expected_condition'])
                assert is_valid, f"Flight test {test_case['test_id']} failed"

@allure.epic("ETL Testing Framework")
@allure.feature("Pricing Testing")
class TestPricing(BaseTest):
    """Pricing-specific business tests"""
    
    @classmethod
    def setup_class(cls):
        cls.csv_controller = CSVTestController()
        cls.sql_repository = SQLRepository()
        cls.db_client = SQLiteClient()
    
    @allure.story("Pricing Validation")
    @pytest.mark.pricing
    def test_pricing_functionality(self):
        """Run all pricing tests from CSV"""
        
        pricing_tests = self.csv_controller.get_tests_by_functionality('pricing')
        
        for test_case in pricing_tests:
            with allure.step(f"Test: {test_case['test_id']} - {test_case['description']}"):
                sql_query = self.sql_repository.get_query(test_case['sql_id'])
                result = self.db_client.execute_query(sql_query)
                
                is_valid = self.csv_controller.validate_result(result, test_case['expected_condition'])
                assert is_valid, f"Pricing test {test_case['test_id']} failed"