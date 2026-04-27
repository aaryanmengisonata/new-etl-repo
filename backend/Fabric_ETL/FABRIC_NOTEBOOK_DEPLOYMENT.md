# Deploy ETL Validation Framework in Microsoft Fabric Notebook

## 1) Upload framework files to Fabric

Upload these files into a Fabric workspace folder or Lakehouse Files path (same folder):

- `fabric_client.py`
- `predefined_validations.py`
- `test_csv_driven_etl_validation.py`
- `fabric_notebook_runner.py`
- `etl_validation_tests.csv`
- `master.properties`

Recommended folder example:
- `/lakehouse/default/Files/etl_framework`

## 2) Update configuration for notebook auth

In `master.properties`, set:

```ini
[FABRIC]
FABRIC_TENANT_ID = <your-tenant-id>
FABRIC_AUTH_METHOD = Notebook
```

Keep your `FABRIC_BRONZE` / `FABRIC_SILVER` SQL endpoints updated.

## 3) Notebook cell: install dependencies

```python
%pip install pandas pyodbc azure-identity allure-pytest
```

Restart session after install if Fabric prompts it.

## 4) Notebook cell: bootstrap paths and env

```python
import os
import sys

FRAMEWORK_DIR = "/lakehouse/default/Files/etl_framework"
sys.path.append(FRAMEWORK_DIR)

os.environ["ETL_CONFIG_PATH"] = f"{FRAMEWORK_DIR}/master.properties"
```

## 5) Notebook cell: smoke test connectivity

```python
from fabric_client import FabricClient

bronze = FabricClient("BRONZE")
silver = FabricClient("SILVER")

print(bronze.execute_query("SELECT TOP 1 1 AS ok"))
print(silver.execute_query("SELECT TOP 1 1 AS ok"))

bronze.close()
silver.close()
```

## 6) Notebook cell: run ETL validations

```python
from fabric_notebook_runner import run_validations

results_df = run_validations(
    test_ids=None,      # e.g. ["TEST_01", "TEST_02"]
    max_tests=5,        # set None or remove for full run
    fail_fast=False,
)

display(results_df)
```

## 7) Notebook cell: fail notebook run when tests fail

```python
failed = results_df[results_df["status"] != "PASSED"]
if not failed.empty:
    raise Exception(f"Validation failures: {len(failed)}")
```

## 8) Schedule in Fabric Pipeline

- Add Notebook activity
- Point to this notebook
- Use pipeline failure handling based on notebook exception from step 7

## Troubleshooting

- `master.properties not found`:
  - Ensure `ETL_CONFIG_PATH` is set to the uploaded file.
- `ODBC Driver 18 for SQL Server is required`:
  - Install/enable runtime with ODBC 18 support.
- Authentication errors:
  - Confirm `FABRIC_AUTH_METHOD = Notebook` and user has access to both SQL endpoints.
