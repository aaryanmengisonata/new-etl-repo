"""
ETL Testing: Bronze to Silver - Comprehensive Validation
Tests: Count of Rows, Deleted Records, Record Count by Max Date, Inserted Records, DP Date Format
"""
import pytest
import allure
from utils.base_test import BaseTest


@allure.feature('Bronze to Silver ETL Validation')
@allure.story('Comprehensive Data Quality Checks')
class TestBronzeToSilverValidation(BaseTest):

    # Table list for validation
    TABLES = [
        'CUSTINVOICEJOUR', 'CUSTINVOICETRANS', 'CUSTTABLE', 'CUSTTRANS', 
        'FISCALCALENDARPERIOD', 'GENERALJOURNALENTRY', 'INVENTTRANS', 
        'LEDGERJOURNALTRANS', 'PURCHLINE', 'SALESLINE', 'SALESTABLE', 
        'VENDINVOICEJOUR', 'VENDTRANS', 'WORKFLOWTRACKINGSTATUSTABLE'
    ]

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title('1. Count of Rows - Bronze to Silver')
    @allure.description('Validates total record count matches for all tables')
    @allure.severity('critical')
    def test_01_count_of_rows(self):
        """Validate total record count matches between Bronze and Silver"""
        
        with allure.step('Query Bronze lakehouse for all table counts'):
            bronze_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_AX_CANADA.fullload.{table}) AS {table}" for table in self.TABLES])}
            """
            bronze_results = self.bronze_client.execute_query(bronze_query)[0]
            allure.attach(str(dict(zip(self.TABLES, bronze_results))), 
                         name='Bronze Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Query Silver lakehouse for all table counts'):
            silver_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_Finance.dbo.{table} WHERE lhname='LH_AX_CANADA') AS {table}" for table in self.TABLES])}
            """
            silver_results = self.silver_client.execute_query(silver_query)[0]
            allure.attach(str(dict(zip(self.TABLES, silver_results))), 
                         name='Silver Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Validate all counts match'):
            mismatches = []
            for i, table in enumerate(self.TABLES):
                if bronze_results[i] != silver_results[i]:
                    mismatches.append(f"{table}: Bronze={bronze_results[i]}, Silver={silver_results[i]}")
            
            assert len(mismatches) == 0, f"Count mismatches found:\n" + "\n".join(mismatches)
            print(f"PASS: All {len(self.TABLES)} tables have matching counts")

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title('2. Deleted Records - Bronze to Silver')
    @allure.description('Validates deleted record count (isdelete=1) matches for all tables')
    @allure.severity('high')
    def test_02_deleted_records(self):
        """Validate deleted record count matches between Bronze and Silver"""
        
        with allure.step('Query Bronze lakehouse for deleted records'):
            bronze_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_AX_CANADA.fullload.{table} WHERE isdelete = 1) AS {table}" for table in self.TABLES])}
            """
            bronze_results = self.bronze_client.execute_query(bronze_query)[0]
            allure.attach(str(dict(zip(self.TABLES, bronze_results))), 
                         name='Bronze Deleted Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Query Silver lakehouse for deleted records'):
            silver_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_Finance.dbo.{table} WHERE isdelete = 1 AND lhname='LH_AX_CANADA') AS {table}" for table in self.TABLES])}
            """
            silver_results = self.silver_client.execute_query(silver_query)[0]
            allure.attach(str(dict(zip(self.TABLES, silver_results))), 
                         name='Silver Deleted Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Validate deleted record counts match'):
            mismatches = []
            for i, table in enumerate(self.TABLES):
                if bronze_results[i] != silver_results[i]:
                    mismatches.append(f"{table}: Bronze={bronze_results[i]}, Silver={silver_results[i]}")
            
            assert len(mismatches) == 0, f"Deleted record count mismatches:\n" + "\n".join(mismatches)
            print(f"PASS: Deleted records match for all {len(self.TABLES)} tables")

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title('3. Record Count by Max Date - Bronze to Silver')
    @allure.description('Validates record count for max created date where created=modified')
    @allure.severity('high')
    def test_03_record_count_by_max_date(self):
        """Validate record count by max date between Bronze and Silver"""
        
        with allure.step('Query Bronze lakehouse for max date records'):
            bronze_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_AX_CANADA.fullload.{table} WHERE dpcreateddatetime=dpmodifieddatetime AND DPCreatedDateTime=(SELECT MAX(dpcreateddatetime) FROM LH_AX_CANADA.fullload.{table})) AS {table}" for table in self.TABLES])}
            """
            bronze_results = self.bronze_client.execute_query(bronze_query)[0]
            allure.attach(str(dict(zip(self.TABLES, bronze_results))), 
                         name='Bronze Max Date Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Query Silver lakehouse for max date records'):
            silver_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_Finance.dbo.{table} WHERE dpcreateddatetime=dpmodifieddatetime AND DPCreatedDateTime=(SELECT MAX(dpcreateddatetime) FROM LH_Finance.dbo.{table} WHERE lhname='LH_AX_CANADA') AND lhname='LH_AX_CANADA') AS {table}" for table in self.TABLES])}
            """
            silver_results = self.silver_client.execute_query(silver_query)[0]
            allure.attach(str(dict(zip(self.TABLES, silver_results))), 
                         name='Silver Max Date Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Validate max date record counts match'):
            mismatches = []
            for i, table in enumerate(self.TABLES):
                if bronze_results[i] != silver_results[i]:
                    mismatches.append(f"{table}: Bronze={bronze_results[i]}, Silver={silver_results[i]}")
            
            assert len(mismatches) == 0, f"Max date record count mismatches:\n" + "\n".join(mismatches)
            print(f"PASS: Max date records match for all {len(self.TABLES)} tables")

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title('4. Inserted Records - Bronze to Silver')
    @allure.description('Validates newly inserted records using recid from Bronze to Silver')
    @allure.severity('normal')
    def test_04_inserted_records(self):
        """Validate inserted records exist in Silver using recids from Bronze"""
        
        with allure.step('Get top 10% inserted records from Bronze with recids'):
            bronze_query = """
            WITH Combined AS (
                SELECT TOP 10 PERCENT 'CUSTINVOICEJOUR' AS TableName, recid, recversion, dpcreateddatetime, dpmodifieddatetime, isdelete
                FROM LH_AX_CANADA.fullload.CUSTINVOICEJOUR
                WHERE dpcreateddatetime = dpmodifieddatetime
                ORDER BY dpmodifieddatetime DESC
                
                UNION ALL
                
                SELECT TOP 10 PERCENT 'CUSTINVOICETRANS', recid, recversion, dpcreateddatetime, dpmodifieddatetime, isdelete
                FROM LH_AX_CANADA.fullload.CUSTINVOICETRANS
                WHERE dpcreateddatetime = dpmodifieddatetime
                ORDER BY dpmodifieddatetime DESC
                
                UNION ALL
                
                SELECT TOP 10 PERCENT 'CUSTTABLE', recid, recversion, dpcreateddatetime, dpmodifieddatetime, isdelete
                FROM LH_AX_CANADA.fullload.CUSTTABLE
                WHERE dpcreateddatetime = dpmodifieddatetime
                ORDER BY dpmodifieddatetime DESC
                
                UNION ALL
                
                SELECT TOP 10 PERCENT 'CUSTTRANS', recid, recversion, dpcreateddatetime, dpmodifieddatetime, isdelete
                FROM LH_AX_CANADA.fullload.CUSTTRANS
                WHERE dpcreateddatetime = dpmodifieddatetime
                ORDER BY dpmodifieddatetime DESC
                
                UNION ALL
                
                SELECT TOP 10 PERCENT 'FISCALCALENDARPERIOD', recid, recversion, dpcreateddatetime, dpmodifieddatetime, isdelete
                FROM LH_AX_CANADA.fullload.FISCALCALENDARPERIOD
                WHERE dpcreateddatetime = dpmodifieddatetime
                ORDER BY dpmodifieddatetime DESC
            )
            SELECT * FROM Combined ORDER BY TableName, dpmodifieddatetime DESC
            """
            bronze_results = self.bronze_client.execute_query(bronze_query)
            
            recids_by_table = {}
            for row in bronze_results:
                table_name = row[0]
                recid = row[1]
                if table_name not in recids_by_table:
                    recids_by_table[table_name] = []
                recids_by_table[table_name].append(str(recid))
            
            allure.attach(str(recids_by_table), name='Bronze RecIDs by Table', attachment_type=allure.attachment_type.JSON)

        with allure.step('Validate records exist in Silver using Bronze recids'):
            union_queries = []
            for table_name, recids in recids_by_table.items():
                recid_list = ','.join(recids)
                union_queries.append(f"""
                SELECT '{table_name}' AS TableName, recid, recversion, dpcreateddatetime, dpmodifieddatetime, isdelete
                FROM LH_Finance.dbo.{table_name}
                WHERE dpcreateddatetime = dpmodifieddatetime AND lhname = 'LH_AX_CANADA' AND recid IN ({recid_list})
                """)
            
            silver_query = f"""
            WITH Combined AS (
                {' UNION ALL '.join(union_queries)}
            )
            SELECT * FROM Combined ORDER BY TableName, dpmodifieddatetime DESC
            """
            
            silver_results = self.silver_client.execute_query(silver_query)
            
            silver_counts = {}
            for row in silver_results:
                table_name = row[0]
                silver_counts[table_name] = silver_counts.get(table_name, 0) + 1
            
            allure.attach(str(silver_counts), name='Silver Matched Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Validate all Bronze recids found in Silver'):
            mismatches = []
            for table_name, bronze_recids in recids_by_table.items():
                bronze_count = len(bronze_recids)
                silver_count = silver_counts.get(table_name, 0)
                if bronze_count != silver_count:
                    mismatches.append(f"{table_name}: Bronze={bronze_count}, Silver={silver_count}")
            
            assert len(mismatches) == 0, f"Inserted record validation failed:\n" + "\n".join(mismatches)
            print(f"PASS: All inserted records from Bronze found in Silver")

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title('5. DP Date Format Validation - Bronze to Silver')
    @allure.description('Validates DPCreatedDateTime and DPModifiedDateTime are not null')
    @allure.severity('normal')
    def test_05_dp_date_format(self):
        """Validate DP date fields are properly populated"""
        
        with allure.step('Query Bronze lakehouse for null DP dates'):
            bronze_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_AX_CANADA.fullload.{table} WHERE dpcreateddatetime IS NULL OR dpmodifieddatetime IS NULL) AS {table}" for table in self.TABLES])}
            """
            bronze_results = self.bronze_client.execute_query(bronze_query)[0]
            allure.attach(str(dict(zip(self.TABLES, bronze_results))), 
                         name='Bronze Null Date Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Query Silver lakehouse for null DP dates'):
            silver_query = f"""
            SELECT 
                {', '.join([f"(SELECT COUNT(*) FROM LH_Finance.dbo.{table} WHERE (dpcreateddatetime IS NULL OR dpmodifieddatetime IS NULL) AND lhname='LH_AX_CANADA') AS {table}" for table in self.TABLES])}
            """
            silver_results = self.silver_client.execute_query(silver_query)[0]
            allure.attach(str(dict(zip(self.TABLES, silver_results))), 
                         name='Silver Null Date Counts', attachment_type=allure.attachment_type.JSON)

        with allure.step('Validate no null DP dates in both layers'):
            bronze_nulls = [f"{self.TABLES[i]}: {bronze_results[i]}" for i in range(len(self.TABLES)) if bronze_results[i] > 0]
            silver_nulls = [f"{self.TABLES[i]}: {silver_results[i]}" for i in range(len(self.TABLES)) if silver_results[i] > 0]
            
            assert len(bronze_nulls) == 0, f"Bronze has null DP dates:\n" + "\n".join(bronze_nulls)
            assert len(silver_nulls) == 0, f"Silver has null DP dates:\n" + "\n".join(silver_nulls)
            print(f"PASS: All DP date fields are properly populated in both layers")
