"""
ETL Testing: Multiple Tables - Bronze to Silver Count Validation
"""
import pytest
import allure
from utils.base_test import BaseTest


@allure.feature('Fabric ETL Testing')
@allure.story('Bronze to Silver Data Validation')
class TestBronzeToSilverCounts(BaseTest):

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title('Validate record counts between Bronze and Silver for multiple tables')
    @allure.description(
        'Compares record counts from LH_AX_CANADA (Bronze) and LH_Finance (Silver) '
        'for multiple Finance tables'
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_multiple_table_count_match(self):
        """Validate record counts for multiple tables between Bronze and Silver"""

        tables = [
            "CUSTINVOICEJOUR",
            "CUSTINVOICETRANS",
            "CUSTTABLE",
            "CUSTTRANS",
            "FISCALCALENDARPERIOD",
        ]

        for table in tables:

            with allure.step(f"Query Bronze lakehouse for {table} record count"):
                bronze_query = f"""
                    SELECT COUNT(*) 
                    FROM LH_AX_CANADA.fullload.{table}
                """
                bronze_count = self.bronze_client.execute_query(bronze_query)[0][0]

                allure.attach(
                    str(bronze_count),
                    name=f"Bronze Count - {table}",
                    attachment_type=allure.attachment_type.TEXT
                )

            with allure.step(f"Query Silver lakehouse for {table} record count"):
                silver_query = f"""
                    SELECT COUNT(*) 
                    FROM LH_Finance.dbo.{table}
                    WHERE lhname = 'LH_AX_CANADA'
                """
                silver_count = self.silver_client.execute_query(silver_query)[0][0]

                allure.attach(
                    str(silver_count),
                    name=f"Silver Count - {table}",
                    attachment_type=allure.attachment_type.TEXT
                )

            with allure.step(f"Validate counts match for {table}"):
                assert bronze_count == silver_count, (
                    f"Count mismatch for {table}: "
                    f"Bronze={bronze_count}, "
                    f"Silver={silver_count}"
                )

                allure.attach(
                    f"Table: {table}\n"
                    f"Bronze: {bronze_count}\n"
                    f"Silver: {silver_count}\n"
                    f"Status: MATCH",
                    name=f"Validation Result - {table}",
                    attachment_type=allure.attachment_type.TEXT
                )

            print(f"PASS: {table} count validation passed: {bronze_count} records")
