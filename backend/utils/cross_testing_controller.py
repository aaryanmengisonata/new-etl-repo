import pandas as pd
import os
import requests
import time

class CrossTestingController:
    def __init__(self, csv_file="cross_testing_example.csv"):
        self.csv_file = csv_file
        self.test_cases = []
        self._load_test_cases()
    
    def _load_test_cases(self):
        """Load test cases from CSV file"""
        if os.path.exists(self.csv_file):
            df = pd.read_csv(self.csv_file)
            self.test_cases = df.to_dict('records')
    
    def get_enabled_tests(self):
        """Get only enabled test cases"""
        return [test for test in self.test_cases if str(test.get('enabled', 'TRUE')).upper() == 'TRUE']
    
    def get_tests_by_type(self, test_type):
        """Get test cases by test type"""
        return [test for test in self.get_enabled_tests() 
                if test.get('test_type', '').upper() == test_type.upper()]
    
    def execute_api_validation(self, test_case):
        """Execute API-specific validation"""
        if test_case['test_id'] == 'API_01':
            # Validate API response count
            response = requests.get("https://fakestoreapi.com/products", verify=False)
            return len(response.json()) if response.status_code == 200 else 0
        elif test_case['test_id'] == 'API_02':
            # Validate API data completeness
            response = requests.get("https://fakestoreapi.com/products", verify=False)
            if response.status_code == 200:
                products = response.json()
                complete_products = [p for p in products if p.get('title') and p.get('price')]
                return len(complete_products)
            return 0
        return 0
    
    def execute_cross_validation(self, test_case, db_client):
        """Execute cross-system validation"""
        if test_case['test_id'] == 'CROSS_01':
            # Compare API count with DB count
            api_response = requests.get("https://fakestoreapi.com/products", verify=False)
            api_count = len(api_response.json()) if api_response.status_code == 200 else 0
            
            db_result = db_client.execute_query("SELECT COUNT(*) FROM products")
            db_count = db_result[0][0] if db_result else 0
            
            return 1 if api_count == db_count else 0
            
        elif test_case['test_id'] == 'CROSS_02':
            # Price consistency validation
            api_response = requests.get("https://fakestoreapi.com/products/1", verify=False)
            api_price = api_response.json().get('price', 0) if api_response.status_code == 200 else 0
            
            db_result = db_client.execute_query("SELECT price FROM products WHERE id = 1")
            db_price = db_result[0][0] if db_result else 0
            
            return 1 if abs(api_price - db_price) < 0.01 else 0
        
        return 0
    
    def execute_performance_test(self, test_case, db_client):
        """Execute performance validation"""
        if test_case['test_id'] == 'PERF_01':
            start_time = time.time()
            db_client.execute_query("SELECT COUNT(*) FROM products")
            execution_time = time.time() - start_time
            return execution_time  # Should be less than threshold
        return 0
    
    def validate_result(self, actual_result, expected_condition, test_case=None):
        """Enhanced validation with cross-testing support"""
        if isinstance(actual_result, list) and len(actual_result) > 0:
            if hasattr(actual_result[0], '__getitem__'):
                actual_value = actual_result[0][0]
            else:
                actual_value = actual_result[0]
        else:
            actual_value = actual_result
        
        condition = expected_condition.upper()
        
        # Dynamic expected values based on test type
        if test_case and test_case.get('test_type') == 'API':
            expected_value = 20  # Expected API product count
        elif test_case and test_case.get('test_type') == 'PERFORMANCE':
            expected_value = 1.0  # Max 1 second
        elif test_case and test_case.get('test_type') == 'CROSS':
            expected_value = 1  # Success indicator
        else:
            expected_value = 0
        
        if condition == 'EQUAL':
            return actual_value == expected_value
        elif condition == 'NOT_EQUAL':
            return actual_value != expected_value
        elif condition == 'GREATER_THAN':
            return actual_value > expected_value
        elif condition == 'LESS_THAN':
            return actual_value < (expected_value if expected_value > 0 else 1000)
        else:
            return False