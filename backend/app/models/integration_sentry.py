from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class SystemDefinition(BaseModel):
    system_type: str = Field(..., description="Either 'database' or 'api'")
    environment: str = Field(..., description="E.g., DEV, QA, PROD")
    
    # For Database
    query: Optional[str] = None
    db_config: Optional[Dict[str, Any]] = None
    
    # For API
    url: Optional[str] = None
    method: Optional[str] = "GET"
    headers: Optional[Dict[str, str]] = None
    payload: Optional[str] = None

class IntegrationScenario(BaseModel):
    id: str
    name: str
    description: str
    type: str = Field(..., description="e.g. data_sync, data_flow, connectivity")

class SystemAnalysisRequest(BaseModel):
    system_a: SystemDefinition
    system_b: SystemDefinition

class SystemAnalysisResponse(BaseModel):
    suggested_scenarios: List[IntegrationScenario]
    system_a_schema: Optional[List[Dict[str, Any]]] = None
    system_b_schema: Optional[List[Dict[str, Any]]] = None
    cross_functional_steps: Optional[List[str]] = None

class ReconciliationRequest(BaseModel):
    system_a: SystemDefinition
    system_b: SystemDefinition
    scenario_id: str
    key_column: Optional[str] = None
    field_mappings: Optional[Dict[str, str]] = None
    row_limit: Optional[int] = 10000
    chunk_size: Optional[int] = 2000
    query_timeout: Optional[int] = 30

class ReconciliationResult(BaseModel):
    passed: bool
    accuracy: float
    matches: int
    mismatches: int
    total_records_a: int
    total_records_b: int
    mismatch_details: List[Dict[str, Any]]
    execution_logs: List[str]
