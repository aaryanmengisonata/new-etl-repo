import allure

from tests.fabric.base_csv_driven_fabric_validation import (
    BaseCSVDrivenETLValidation,
)


@allure.epic("ETL Testing Framework")
@allure.feature("CSV-Driven Silver To Gold Validation")
class TestCSVDrivenSilverToGoldValidation(BaseCSVDrivenETLValidation):
    """CSV-driven ETL validation for Silver to Gold."""

    __test__ = True
    CSV_FILE = "data/etl_validation_silver_to_gold_tests.csv"
    SOURCE_LAYER = "SILVER"
    TARGET_LAYER = "GOLD"
