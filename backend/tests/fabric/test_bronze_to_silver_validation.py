"""
ETL Testing: Bronze to Silver Layer Validation
Table: customer_data (example)
"""
import pytest
from utils.base_test import BaseTest

class TestBronzeToSilver(BaseTest):
    
    # Replace with your actual table names
    BRONZE_TABLE = "bronze.customer_data"
    SILVER_TABLE = "silver.customer_data"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_record_count_match(self):
        """Validate total record count matches between Bronze and Silver"""
        bronze_count = self.bronze_client.execute_query(f"SELECT COUNT(*) FROM {self.BRONZE_TABLE}")[0][0]
        silver_count = self.silver_client.execute_query(f"SELECT COUNT(*) FROM {self.SILVER_TABLE}")[0][0]
        
        assert bronze_count == silver_count, f"Count mismatch: Bronze={bronze_count}, Silver={silver_count}"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_no_duplicate_records(self):
        """Validate no duplicate records in Silver based on primary key"""
        query = f"""
        SELECT customer_id, COUNT(*) as cnt 
        FROM {self.SILVER_TABLE} 
        GROUP BY customer_id 
        HAVING COUNT(*) > 1
        """
        duplicates = self.silver_client.execute_query(query)
        
        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate customer_ids in Silver"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_no_null_primary_keys(self):
        """Validate no NULL values in primary key column"""
        null_count = self.silver_client.execute_query(
            f"SELECT COUNT(*) FROM {self.SILVER_TABLE} WHERE customer_id IS NULL"
        )[0][0]
        
        assert null_count == 0, f"Found {null_count} NULL primary keys in Silver"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_data_completeness(self):
        """Validate critical columns have no NULL values"""
        query = f"""
        SELECT 
            SUM(CASE WHEN customer_name IS NULL THEN 1 ELSE 0 END) as null_names,
            SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) as null_emails,
            SUM(CASE WHEN created_date IS NULL THEN 1 ELSE 0 END) as null_dates
        FROM {self.SILVER_TABLE}
        """
        result = self.silver_client.execute_query(query)[0]
        
        assert result[0] == 0, f"Found {result[0]} NULL customer names"
        assert result[1] == 0, f"Found {result[1]} NULL emails"
        assert result[2] == 0, f"Found {result[2]} NULL created dates"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_data_transformation_accuracy(self):
        """Validate aggregated values match between Bronze and Silver"""
        bronze_sum = self.bronze_client.execute_query(
            f"SELECT SUM(total_amount) FROM {self.BRONZE_TABLE}"
        )[0][0]
        
        silver_sum = self.silver_client.execute_query(
            f"SELECT SUM(total_amount) FROM {self.SILVER_TABLE}"
        )[0][0]
        
        assert bronze_sum == silver_sum, f"Sum mismatch: Bronze={bronze_sum}, Silver={silver_sum}"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_date_range_validation(self):
        """Validate date ranges are within expected bounds"""
        query = f"""
        SELECT 
            MIN(created_date) as min_date,
            MAX(created_date) as max_date
        FROM {self.SILVER_TABLE}
        """
        result = self.silver_client.execute_query(query)[0]
        
        assert result[0] is not None, "Min date is NULL"
        assert result[1] is not None, "Max date is NULL"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_data_type_validation(self):
        """Validate email format in Silver"""
        invalid_emails = self.silver_client.execute_query(f"""
        SELECT COUNT(*) 
        FROM {self.SILVER_TABLE} 
        WHERE email NOT LIKE '%@%.%'
        AND email IS NOT NULL
        """)[0][0]
        
        assert invalid_emails == 0, f"Found {invalid_emails} invalid email formats"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_referential_integrity(self):
        """Validate all Bronze records exist in Silver"""
        query = f"""
        SELECT COUNT(*) 
        FROM {self.BRONZE_TABLE} b
        LEFT JOIN {self.SILVER_TABLE} s ON b.customer_id = s.customer_id
        WHERE s.customer_id IS NULL
        """
        missing_records = self.bronze_client.execute_query(query)[0][0]
        
        assert missing_records == 0, f"Found {missing_records} records in Bronze missing from Silver"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_data_freshness(self):
        """Validate Silver has recent data (loaded today)"""
        query = f"""
        SELECT COUNT(*) 
        FROM {self.SILVER_TABLE} 
        WHERE CAST(load_timestamp AS DATE) = CAST(GETDATE() AS DATE)
        """
        today_records = self.silver_client.execute_query(query)[0][0]
        
        assert today_records > 0, "No records loaded today in Silver"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_negative_values_check(self):
        """Validate no negative values in amount columns"""
        negative_count = self.silver_client.execute_query(f"""
        SELECT COUNT(*) 
        FROM {self.SILVER_TABLE} 
        WHERE total_amount < 0
        """)[0][0]
        
        assert negative_count == 0, f"Found {negative_count} negative amounts in Silver"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_status_values_validation(self):
        """Validate status column has only allowed values"""
        invalid_status = self.silver_client.execute_query(f"""
        SELECT COUNT(*) 
        FROM {self.SILVER_TABLE} 
        WHERE status NOT IN ('Active', 'Inactive', 'Pending')
        """)[0][0]
        
        assert invalid_status == 0, f"Found {invalid_status} invalid status values"
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_schema_column_count(self):
        """Validate Silver has expected number of columns"""
        column_count = self.silver_client.execute_query(f"""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{self.SILVER_TABLE.split('.')[1]}'
        """)[0][0]
        
        expected_columns = 10  # Update with your expected count
        assert column_count == expected_columns, f"Expected {expected_columns} columns, found {column_count}"
