import pandas as pd
import os

class CSVTestController:
    def __init__(self, csv_file="test_cases.csv"):
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
    
    def get_tests_by_functionality(self, functionality):
        """Get test cases for specific functionality"""
        return [test for test in self.get_enabled_tests() 
                if test.get('functionality', '').lower() == functionality.lower()]
    
    def get_test_by_id(self, test_id):
        """Get specific test case by ID"""
        for test in self.test_cases:
            if test.get('test_id') == test_id:
                return test
        return None
    
    def validate_result(self, actual_result, expected_condition, expected_value=None):
        """Validate test result based on condition"""
        # Handle SQLite Row objects
        if isinstance(actual_result, list) and len(actual_result) > 0:
            if hasattr(actual_result[0], '__getitem__'):
                actual_value = actual_result[0][0]
            else:
                actual_value = actual_result[0]
        else:
            actual_value = actual_result
        
        condition = expected_condition.upper()
        
        if condition == 'EQUAL':
            return actual_value == (expected_value or 0)
        elif condition == 'NOT_EQUAL':
            return actual_value != (expected_value or 0)
        elif condition == 'GREATER_THAN':
            return actual_value > (expected_value or 0)
        elif condition == 'LESS_THAN':
            return actual_value < (expected_value or 1000)
        else:
            return False