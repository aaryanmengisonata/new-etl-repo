from typing import Dict

from pydantic import BaseModel, Field


class LayerConfig(BaseModel):
    lakehouse: str = ""
    endpoint: str = ""


class EnvironmentConfig(BaseModel):
    bronze: LayerConfig = Field(default_factory=LayerConfig)
    silver: LayerConfig = Field(default_factory=LayerConfig)
    gold: LayerConfig = Field(default_factory=LayerConfig)


class ConfigUpdate(BaseModel):
    FABRIC_LAYER: str
    FABRIC_ENV: str
    FABRIC_LAKEHOUSE: str
    FABRIC_ENDPOINT: str
    FABRIC_CONFIGS: Dict[str, EnvironmentConfig] = Field(default_factory=dict)

class DbConnectionConfig(BaseModel):
    engine: str = "sqlite"
    host: str = "localhost"
    port: str = "5432"
    db_name: str = "etl_test.db"
    username: str = ""
    password: str = ""


class DbConfigUpdate(DbConnectionConfig):
    pass


class PipelineConfig(BaseModel):
    default_row_limit: int = 10000
    default_chunk_size: int = 2000
    default_query_timeout: int = 30
    default_source_db: str = "test_audit_src_test.db"
    default_target_db: str = "test_audit_tgt_test.db"


class ApiSentryConfig(BaseModel):
    base_url: str = "https://fakestoreapi.com"
    timeout: int = 30
    ssl_verify: bool = False


class IntegrationConfig(BaseModel):
    source_db: str = "test_audit_src_test.db"
    target_db: str = "test_audit_tgt_test.db"
    key_column: str = "id"
    reconciliation_type: str = "data_diff"


class TestingConfig(BaseModel):
    csv_file: str = "test_cases.csv"
    sql_dir: str = "sql"
    report_dir: str = "reports"
    enable_parallel: bool = False
    max_workers: int = 4


class ReportingConfig(BaseModel):
    allure_results: str = "reports/allure-results"
    xml_results: str = "reports/xml-results"
    generate_xml: bool = True
    generate_html: bool = True
