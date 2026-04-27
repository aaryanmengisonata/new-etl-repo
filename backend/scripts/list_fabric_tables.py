"""
Helper script to list available tables in Fabric lakehouses
"""
from utils.fabric_client import FabricClient

print("Connecting to Bronze lakehouse...")
bronze = FabricClient('BRONZE')

print("\n=== BRONZE LAKEHOUSE TABLES ===")
try:
    tables = bronze.execute_query("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    for schema, table in tables:
        print(f"  {schema}.{table}")
except Exception as e:
    print(f"Error: {e}")

print("\n\nConnecting to Silver lakehouse...")
silver = FabricClient('SILVER')

print("\n=== SILVER LAKEHOUSE TABLES ===")
try:
    tables = silver.execute_query("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    for schema, table in tables:
        print(f"  {schema}.{table}")
except Exception as e:
    print(f"Error: {e}")

bronze.close()
silver.close()
