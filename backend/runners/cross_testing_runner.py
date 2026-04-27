#!/usr/bin/env python3
"""
Cross-Testing Runner - Excel/CSV Controlled Testing Across All Areas
Demonstrates API + Database + ETL + Integration testing from single Excel file
"""

import sys
import time
import argparse
from utils.cross_testing_controller import CrossTestingController
from utils.sql_repository import SQLRepository
from utils.sqlite_client import SQLiteClient
from utils.xml_reporter import XMLReportGenerator
from utils.api_client import APIClient

class CrossTestingRunner:
    def __init__(self):
        self.controller = CrossTestingController()
        self.sql_repo = SQLRepository("sql")
        self.db_client = SQLiteClient()
        self.api_client = APIClient()
        self.xml_reporter = XMLReportGenerator()
        
        # Load cross-testing SQL queries
        self._load_cross_queries()
    
    def _load_cross_queries(self):
        """Load cross-testing specific queries"""
        import os
        cross_sql_file = "sql/cross_testing_queries.sql"
        if os.path.exists(cross_sql_file):
            with open(cross_sql_file, 'r') as f:
                queries = [q.strip() for q in f.read().split(';') if q.strip()]
                for i, query in enumerate(queries, 1):
                    if query:
                        self.sql_repo.queries[str(i)] = query + ';'
    
    def run_cross_testing_demo(self):
        """Run comprehensive cross-testing demonstration"""
        print("=" * 60)
        print("CROSS-TESTING DEMONSTRATION - Excel/CSV Controlled")
        print("=" * 60)
        print("Testing Areas: API + Database + ETL + Integration")
        print("Control Method: Excel/CSV file")
        print("=" * 60)
        
        test_cases = self.controller.get_enabled_tests()
        results = {}
        
        for test_case in test_cases:
            test_id = test_case['test_id']
            test_type = test_case.get('test_type', 'UNKNOWN')
            description = test_case.get('description', '')
            
            print(f"\n[{test_type}] Executing: {test_id}")
            print(f"Description: {description}")
            
            start_time = time.time()
            
            try:
                result = self._execute_test_by_type(test_case)
                execution_time = time.time() - start_time
                
                is_valid = self.controller.validate_result(
                    result, test_case['expected_condition'], test_case
                )
                
                status = "PASSED" if is_valid else "FAILED"
                print(f"Result: {result} | Status: {status}")
                
                results[test_id] = {
                    'status': status,
                    'result': result,
                    'execution_time': execution_time,
                    'test_type': test_type
                }
                
                self.xml_reporter.add_test_result(
                    test_id, test_type, 'PASSED' if is_valid else 'FAILED', 
                    execution_time, None if is_valid else f"Expected: {test_case['expected_condition']}, Got: {result}"
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"ERROR: {str(e)}")
                results[test_id] = {
                    'status': 'ERROR',
                    'result': str(e),
                    'execution_time': execution_time,
                    'test_type': test_type
                }
                
                self.xml_reporter.add_test_result(
                    test_id, test_type, 'FAILED', execution_time, str(e)
                )
        
        self._generate_cross_testing_report(results)
    
    def _execute_test_by_type(self, test_case):
        """Execute test based on type"""
        test_type = test_case.get('test_type', '').upper()
        
        if test_type == 'API':
            return self.controller.execute_api_validation(test_case)
        elif test_type == 'CROSS':
            return self.controller.execute_cross_validation(test_case, self.db_client)
        elif test_type == 'PERFORMANCE':
            return self.controller.execute_performance_test(test_case, self.db_client)
        else:
            # Standard database/ETL/integration tests
            sql_id = test_case.get('sql_id')
            sql_query = self.sql_repo.get_query(sql_id)
            if sql_query:
                return self.db_client.execute_query(sql_query)
            return 0
    
    def _generate_cross_testing_report(self, results):
        """Generate comprehensive cross-testing report"""
        print("\n" + "=" * 60)
        print("CROSS-TESTING RESULTS SUMMARY")
        print("=" * 60)
        
        # Group by test type
        by_type = {}
        for test_id, result in results.items():
            test_type = result['test_type']
            if test_type not in by_type:
                by_type[test_type] = {'passed': 0, 'failed': 0, 'total': 0}
            
            by_type[test_type]['total'] += 1
            if result['status'] == 'PASSED':
                by_type[test_type]['passed'] += 1
            else:
                by_type[test_type]['failed'] += 1
        
        # Display results by type
        for test_type, stats in by_type.items():
            pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{test_type:15} | Total: {stats['total']:2} | Passed: {stats['passed']:2} | Failed: {stats['failed']:2} | Rate: {pass_rate:5.1f}%")
        
        # Overall summary
        total_tests = sum([stats['total'] for stats in by_type.values()])
        total_passed = sum([stats['passed'] for stats in by_type.values()])
        overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print("-" * 60)
        print(f"OVERALL RESULTS | Total: {total_tests} | Passed: {total_passed} | Rate: {overall_rate:.1f}%")
        
        # Generate XML report
        xml_file = self.xml_reporter.generate_xml_report("cross_testing_results.xml")
        print(f"\nXML Report: {xml_file}")
        
        print("\n" + "=" * 60)
        print("CROSS-TESTING DEMONSTRATION COMPLETE!")
        print("Excel/CSV successfully controlled all testing areas!")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Cross-Testing Runner')
    parser.add_argument('--demo', action='store_true', help='Run cross-testing demonstration')
    
    args = parser.parse_args()
    
    runner = CrossTestingRunner()
    
    if args.demo or len(sys.argv) == 1:
        runner.run_cross_testing_demo()

if __name__ == "__main__":
    main()