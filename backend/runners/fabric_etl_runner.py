#!/usr/bin/env python3
"""
Fabric ETL Test Runner - Tests Bronze -> Silver -> Gold pipeline
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fabric_client import FabricClient
from utils.xml_reporter import XMLReportGenerator

class FabricETLRunner:
    def __init__(self):
        self.bronze = FabricClient('BRONZE')
        self.silver = FabricClient('SILVER')
        self.gold = FabricClient('GOLD')
        self.reporter = XMLReportGenerator()
        
    def test_bronze_to_silver(self, source_table, target_table, validation_query=None):
        """Test data movement from Bronze to Silver"""
        print(f"Testing Bronze -> Silver: {source_table} -> {target_table}")
        start_time = time.time()
        
        try:
            bronze_count = self.bronze.execute_query(f"SELECT COUNT(*) FROM {source_table}")[0][0]
            silver_count = self.silver.execute_query(f"SELECT COUNT(*) FROM {target_table}")[0][0]
            
            if validation_query:
                validation_result = self.silver.execute_query(validation_query)
                assert validation_result, "Validation query failed"
            
            assert bronze_count == silver_count, f"Count mismatch: Bronze={bronze_count}, Silver={silver_count}"
            
            execution_time = time.time() - start_time
            self.reporter.add_test_result(f"Bronze_to_Silver_{source_table}", "ETL", "PASSED", execution_time)
            print(f"   PASSED - Records: {bronze_count}")
            return True
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_test_result(f"Bronze_to_Silver_{source_table}", "ETL", "FAILED", execution_time, str(e))
            print(f"   FAILED - {str(e)}")
            return False
    
    def test_silver_to_gold(self, source_table, target_table, validation_query=None):
        """Test data movement from Silver to Gold"""
        print(f"Testing Silver -> Gold: {source_table} -> {target_table}")
        start_time = time.time()
        
        try:
            silver_count = self.silver.execute_query(f"SELECT COUNT(*) FROM {source_table}")[0][0]
            gold_count = self.gold.execute_query(f"SELECT COUNT(*) FROM {target_table}")[0][0]
            
            if validation_query:
                validation_result = self.gold.execute_query(validation_query)
                assert validation_result, "Validation query failed"
            
            assert silver_count == gold_count, f"Count mismatch: Silver={silver_count}, Gold={gold_count}"
            
            execution_time = time.time() - start_time
            self.reporter.add_test_result(f"Silver_to_Gold_{source_table}", "ETL", "PASSED", execution_time)
            print(f"   PASSED - Records: {silver_count}")
            return True
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_test_result(f"Silver_to_Gold_{source_table}", "ETL", "FAILED", execution_time, str(e))
            print(f"   FAILED - {str(e)}")
            return False
    
    def run_full_pipeline_test(self, bronze_table, silver_table, gold_table):
        """Test complete Bronze -> Silver -> Gold pipeline"""
        print(f"\n{'='*60}")
        print(f"Testing Full Pipeline: {bronze_table} -> {silver_table} -> {gold_table}")
        print(f"{'='*60}")
        
        result1 = self.test_bronze_to_silver(bronze_table, silver_table)
        result2 = self.test_silver_to_gold(silver_table, gold_table)
        
        if result1 and result2:
            print(f"   FULL PIPELINE PASSED")
        else:
            print(f"   FULL PIPELINE FAILED")
        
        return result1 and result2
    
    def generate_report(self):
        """Generate XML report"""
        xml_file = self.reporter.generate_xml_report()
        print(f"\nReport generated: {xml_file}")

if __name__ == "__main__":
    runner = FabricETLRunner()
    
    # Example: Test your pipeline
    # runner.run_full_pipeline_test('bronze_products', 'silver_products', 'gold_products')
    
    runner.generate_report()
