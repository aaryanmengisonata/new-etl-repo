# ETL Metrics Dashboard (Allure Custom Tab)

This project now includes a custom Allure tab: **ETL Metrics Dashboard**.

## Plugin Location
- Source (versioned): `plugins/etl-metrics-dashboard-plugin`
- Installed target: `allure-2.32.0/plugins/etl-metrics-dashboard-plugin`

## Install Plugin
```powershell
.\scripts\install_allure_etl_dashboard_plugin.ps1
```

## How Data Is Loaded
1. During test execution, `tests/conftest.py` (`pytest_sessionfinish`) prepares dashboard data.
2. If `allure-results/etl-metrics-dashboard-input.json` exists, that JSON is used.
3. Otherwise, data is auto-built from test labels:
   - `Source_Count`
   - `Target_Count`
   - `Table`
   - `Source_Lakehouse`
   - `Target_Lakehouse`
   - `Validation`
4. The final file `etl-metrics-dashboard-attachment.json` is linked as an Allure JSON attachment, so `allure generate` and `allure serve` include it automatically.

## Custom JSON Format
Use the structure in:
- `data/etl_metrics_dashboard_input.sample.json`

At runtime place your file at:
- `allure-results/etl-metrics-dashboard-input.json`

## Run
```powershell
.\scripts\install_allure_etl_dashboard_plugin.ps1
python -m pytest tests/fabric/test_csv_driven_etl_validation.py --alluredir=allure-results
.\allure-2.32.0\bin\allure.bat generate allure-results -o reports\allure-report --clean
.\allure-2.32.0\bin\allure.bat serve allure-results
```

After generation/serve, open tab **ETL Metrics Dashboard**.

## Client Share (Single HTML)
For client sharing with one double-click file (no local server), generate a standalone HTML report:

```powershell
python .\scripts\generate_client_html_report.py
```

Output:
- `reports/client-report/index.html`

You can also run:

```powershell
.\scripts\build_client_report.bat
```

The generated file embeds ETL metrics data and can be opened directly from `file://` by double-clicking `index.html`.
