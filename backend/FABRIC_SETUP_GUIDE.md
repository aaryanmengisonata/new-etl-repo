# Fabric ETL Testing Framework - Setup Guide

## Prerequisites
- Python 3.8 or higher
- Access to Microsoft Fabric workspace
- Azure tenant ID
- ODBC Driver 18 for SQL Server

## Step 1: Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Install ODBC Driver

### Windows:
Download and install from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Linux:
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Mac:
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

## Step 3: Get Fabric Connection Details

From Microsoft Fabric portal, collect:

1. **Tenant ID**: Azure Portal → Azure Active Directory → Overview → Tenant ID
2. **SQL Endpoints**: Fabric Workspace → Lakehouse → Settings → SQL analytics endpoint
3. **Lakehouse Names**: Your Bronze, Silver, Gold lakehouse names

## Step 4: Configure Framework

Edit `config/master.properties`:

```properties
[FABRIC]
FABRIC_TENANT_ID = <your_tenant_id>
FABRIC_AUTH_METHOD = Interactive

[FABRIC_BRONZE]
BRONZE_LAKEHOUSE_NAME = <your_bronze_lakehouse_name>
BRONZE_SQL_ENDPOINT = <xxxxx.datawarehouse.fabric.microsoft.com>

[FABRIC_SILVER]
SILVER_LAKEHOUSE_NAME = <your_silver_lakehouse_name>
SILVER_SQL_ENDPOINT = <xxxxx.datawarehouse.fabric.microsoft.com>

[FABRIC_GOLD]
GOLD_LAKEHOUSE_NAME = <your_gold_lakehouse_name>
GOLD_SQL_ENDPOINT = <xxxxx.datawarehouse.fabric.microsoft.com>
```

## Step 5: Update Test Files

Edit `tests/fabric/test_bronze_to_silver_validation.py`:

```python
# Update table names (line 10-11)
BRONZE_TABLE = "bronze.your_table_name"
SILVER_TABLE = "silver.your_table_name"

# Update column names throughout the file to match your schema
```

## Step 6: Run Tests

### Run all Fabric tests:
```bash
pytest tests/fabric/ -v
```

### Run specific test:
```bash
pytest tests/fabric/test_bronze_to_silver_validation.py -v
```

### Run with markers:
```bash
pytest -m fabric -v
pytest -m etl -v
```

### Generate Allure report:
```bash
pytest tests/fabric/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

## Step 7: View Reports

Reports are generated in:
- **XML Reports**: `reports/xml-results/`
- **Allure Reports**: `reports/allure-results/`
- **HTML Reports**: `reports/`

## Authentication Flow

When you run tests:
1. Browser window opens automatically
2. Login with your Microsoft credentials
3. Complete MFA authentication
4. Tests execute automatically
5. Browser can be closed after authentication

## Troubleshooting

### Issue: ODBC Driver not found
**Solution**: Install ODBC Driver 18 for SQL Server (see Step 2)

### Issue: Authentication fails
**Solution**: 
- Verify FABRIC_TENANT_ID is correct
- Ensure you have access to the Fabric workspace
- Check your user has Reader/Contributor role

### Issue: Connection timeout
**Solution**: 
- Verify SQL endpoints are correct
- Check network connectivity
- Ensure firewall allows outbound connections

### Issue: Table not found
**Solution**: 
- Verify table names in test files
- Check lakehouse has the tables
- Ensure proper schema prefix (bronze.table_name)

## Quick Start Commands

```bash
# Complete setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configure (edit config/master.properties with your details)

# Run tests
pytest tests/fabric/ -v

# Generate report
pytest tests/fabric/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

## For CI/CD (Service Principal Required)

Update `config/master.properties`:
```properties
[FABRIC]
FABRIC_TENANT_ID = <tenant_id>
FABRIC_CLIENT_ID = <service_principal_client_id>
FABRIC_CLIENT_SECRET = <service_principal_secret>
FABRIC_AUTH_METHOD = ServicePrincipal
```

Then run in pipeline:
```bash
pytest tests/fabric/ --junitxml=reports/junit.xml
```

## Support

For issues or questions, refer to:
- Framework README.md
- Microsoft Fabric documentation
- Azure authentication documentation
