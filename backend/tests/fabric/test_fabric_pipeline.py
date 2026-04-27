"""
Fabric Pipeline ETL Tests - Bronze -> Silver -> Gold
"""
import pytest
from utils.base_test import BaseTest

class TestFabricPipeline(BaseTest):
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_bronze_to_silver_record_count(self):
        """Validate record count from Bronze to Silver"""
        bronze_count = self.bronze_client.execute_query("SELECT COUNT(*) FROM your_bronze_table")[0][0]
        silver_count = self.silver_client.execute_query("SELECT COUNT(*) FROM your_silver_table")[0][0]
        
        assert bronze_count == silver_count, f"Record count mismatch: Bronze={bronze_count}, Silver={silver_count}"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_silver_to_gold_record_count(self):
        """Validate record count from Silver to Gold"""
        silver_count = self.silver_client.execute_query("SELECT COUNT(*) FROM your_silver_table")[0][0]
        gold_count = self.gold_client.execute_query("SELECT COUNT(*) FROM your_gold_table")[0][0]
        
        assert silver_count == gold_count, f"Record count mismatch: Silver={silver_count}, Gold={gold_count}"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_data_quality_silver(self):
        """Validate data quality in Silver layer"""
        null_check = self.silver_client.execute_query(
            "SELECT COUNT(*) FROM your_silver_table WHERE key_column IS NULL"
        )[0][0]
        
        assert null_check == 0, f"Found {null_check} null values in key column"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_data_transformation_silver_to_gold(self):
        """Validate data transformations from Silver to Gold"""
        silver_sum = self.silver_client.execute_query("SELECT SUM(amount) FROM your_silver_table")[0][0]
        gold_sum = self.gold_client.execute_query("SELECT SUM(amount) FROM your_gold_table")[0][0]
        
        assert silver_sum == gold_sum, f"Sum mismatch: Silver={silver_sum}, Gold={gold_sum}"
