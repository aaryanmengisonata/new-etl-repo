@echo off
echo === ETL Framework - Allure Test Execution ===

echo 1. Cleaning previous results...
if exist "reports\allure-results" rmdir /s /q "reports\allure-results"
mkdir "reports\allure-results"

echo 2. Running tests with Allure...
set PYTHONPATH=%cd%
python -m pytest tests/etl/test_etl_allure.py tests/api/test_api_allure.py --alluredir=reports/allure-results -v

echo 3. Test execution completed!
echo 4. To view Allure report, install Allure CLI and run:
echo    allure serve reports/allure-results

echo.
echo Alternative: Generate static report with:
echo    allure generate reports/allure-results -o reports/allure-report --clean
echo    Then open: reports/allure-report/index.html

pause