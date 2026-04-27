#!/usr/bin/env python3
"""
ETL Test Runner - Production Style
Mimics the existing ETL framework approach with CSV control and XML reporting
"""

import sys
import os
import time
import argparse
import configparser

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_controller import CSVTestController
from utils.sql_repository import SQLRepository
from utils.sqlite_client import SQLiteClient
from utils.xml_reporter import XMLReportGenerator

class ETLTestRunner:
    def __init__(self, config_file="config/master.properties"):
        self.config = self._load_config(config_file)
        self.csv_controller = CSVTestController("data/test_cases.csv")
        self.sql_repository = SQLRepository()
        self.db_client = SQLiteClient()
        self.xml_reporter = XMLReportGenerator()
        
    def _load_config(self, config_file):
        """Load master configuration"""
        config = configparser.ConfigParser()
        config.read(config_file)
        return config
    
    def run_all_tests(self):
        """Run all enabled tests from CSV"""
        print("Starting ETL Test Execution...")
        print("=" * 50)
        
        test_cases = self.csv_controller.get_enabled_tests()
        total_tests = len(test_cases)
        passed_tests = 0
        failed_tests = 0
        
        print(f"Total test cases to execute: {total_tests}")
        print("=" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            test_id = test_case['test_id']
            functionality = test_case['functionality']
            sql_id = test_case['sql_id']
            expected_condition = test_case['expected_condition']
            
            print(f"[{i}/{total_tests}] Executing: {test_id} ({functionality})")
            
            start_time = time.time()
            
            try:
                # Get and execute SQL
                sql_query = self.sql_repository.get_query(sql_id)
                if not sql_query:
                    raise Exception(f"SQL query not found for ID: {sql_id}")
                
                result = self.db_client.execute_query(sql_query)
                
                # Validate result
                is_valid = self.csv_controller.validate_result(result, expected_condition)
                
                execution_time = time.time() - start_time
                
                if is_valid:
                    print(f"   PASSED - {test_case.get('description', '')}")
                    passed_tests += 1
                    self.xml_reporter.add_test_result(test_id, functionality, 'PASSED', execution_time)
                else:
                    print(f"   FAILED - Expected: {expected_condition}, Got: {result}")
                    failed_tests += 1
                    self.xml_reporter.add_test_result(test_id, functionality, 'FAILED', execution_time, 
                                                    f"Expected: {expected_condition}, Got: {result}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"   ERROR - {str(e)}")
                failed_tests += 1
                self.xml_reporter.add_test_result(test_id, functionality, 'FAILED', execution_time, str(e))
        
        # Generate reports
        self._generate_reports(total_tests, passed_tests, failed_tests)
    
    def run_functionality_tests(self, functionality):
        """Run tests for specific functionality"""
        print(f"Running {functionality.upper()} tests...")
        
        test_cases = self.csv_controller.get_tests_by_functionality(functionality)
        if not test_cases:
            print(f"No tests found for functionality: {functionality}")
            return
        
        for test_case in test_cases:
            self._execute_single_test(test_case)
    
    def run_single_test(self, test_id):
        """Run single test by ID"""
        print(f"Running single test: {test_id}")
        
        test_case = self.csv_controller.get_test_by_id(test_id)
        if not test_case:
            print(f"Test not found: {test_id}")
            return
        
        self._execute_single_test(test_case)
    
    def _execute_single_test(self, test_case):
        """Execute a single test case"""
        test_id = test_case['test_id']
        sql_id = test_case['sql_id']
        expected_condition = test_case['expected_condition']
        
        try:
            sql_query = self.sql_repository.get_query(sql_id)
            result = self.db_client.execute_query(sql_query)
            is_valid = self.csv_controller.validate_result(result, expected_condition)
            
            status = "PASSED" if is_valid else "FAILED"
            print(f"   {test_id}: {status}")
            
        except Exception as e:
            print(f"   {test_id}: ERROR - {str(e)}")
    
    def _generate_reports(self, total, passed, failed):
        """Generate test reports"""
        print("\n" + "=" * 50)
        print("TEST EXECUTION SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        # Generate XML report
        xml_file = self.xml_reporter.generate_xml_report()
        print(f"\nXML Report generated: {xml_file}")
        
        # Generate summary
        summary = self.xml_reporter.generate_summary_report()
        print(f"Total execution time: {summary['execution_time']:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description='ETL Test Runner')
    parser.add_argument('--functionality', '-f', help='Run tests for specific functionality')
    parser.add_argument('--test-id', '-t', help='Run single test by ID')
    parser.add_argument('--config', '-c', default='config/master.properties', help='Configuration file')
    
    args = parser.parse_args()
    
    runner = ETLTestRunner(args.config)
    
    if args.test_id:
        runner.run_single_test(args.test_id)
    elif args.functionality:
        runner.run_functionality_tests(args.functionality)
    else:
        runner.run_all_tests()

if __name__ == "__main__":
    main()