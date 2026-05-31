import pytest
import logging
import yaml
from utils.api_client import APIClient
from utils.sqlite_client import SQLiteClient
from utils.fabric_client import FabricClient
from utils.sqlserver_client import SQLServerClient

class BaseTest:
    @pytest.fixture(autouse=True)
    def setup(self):
        import os
        from utils.db_client import DatabaseClient
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Dynamically set API Client from env
        api_base_url = os.getenv('API_BASE_URL', "https://fakestoreapi.com")
        self.api_client = APIClient(api_base_url)
        
        # Dynamically set DB Client based on DB_TYPE (default to sqlite for backward compatibility)
        db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        if db_type == 'postgres':
            self.db_client = DatabaseClient()
        elif db_type == 'sqlserver':
            self.db_client = SQLServerClient('CUSTOMER_DB')
        else:
            self.db_client = SQLiteClient()
        
        # Fabric clients for Bronze, Silver, Gold
        self.bronze_client = FabricClient('BRONZE')
        self.silver_client = FabricClient('SILVER')
        self.gold_client = FabricClient('GOLD')
        
        # AX SQL Server client
        self.ax_client = SQLServerClient('AX_SOURCE')
        
        # Load config
        with open('config/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
    
    def validate_response_status(self, response, expected_status=200):
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    
    def validate_response_schema(self, response_data, schema):
        from jsonschema import validate
        validate(instance=response_data, schema=schema)
    
    def validate_required_fields(self, data, required_fields):
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing"