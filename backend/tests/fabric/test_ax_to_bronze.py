"""
ETL Testing: AX SQL Server to Bronze Lakehouse Validation
"""

import pytest
import allure
from utils.base_test import BaseTest


@allure.feature("AX to Fabric ETL Testing")
@allure.story("AX SQL Server to Bronze Lakehouse Validation")
class TestAXToBronze(BaseTest):

    @pytest.mark.fabric
    @pytest.mark.etl
    @allure.title("Validate CUSTINVOICEJOUR count from AX to Bronze")
    @allure.description(
        "Validates record count between AX SQL Server and Bronze Lakehouse (LH_AX_CANADA)"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ax_to_bronze_count_match(self):
        """Validate CUSTINVOICEJOUR record count matches between AX and Bronze"""

        with allure.step("Query AX SQL Server for record count"):
            ax_query = """
            SELECT COUNT(*)
            FROM dbo.CUSTINVOICEJOUR
            WHERE MODIFIEDDATETIME >= '2019-01-01'
            """
            ax_count = self.ax_client.execute_query(ax_query)[0][0]
            allure.attach(
                str(ax_count),
                name="AX Count",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Query Bronze Lakehouse for record count"):
            bronze_query = """
            SELECT COUNT(*)
            FROM fullload.CUSTINVOICEJOUR
            """
            bronze_count = self.bronze_client.execute_query(bronze_query)[0][0]
            allure.attach(
                str(bronze_count),
                name="Bronze Count",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Validate counts match"):
            assert ax_count == bronze_count, (
                f"Count mismatch: AX={ax_count}, Bronze={bronze_count}"
            )

            allure.attach(
                f"AX: {ax_count}\nBronze: {bronze_count}\nStatus: MATCH",
                name="Validation Result",
                attachment_type=allure.attachment_type.TEXT,
            )

        print(f"PASS: AX to Bronze validation passed: {ax_count} records")
