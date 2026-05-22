from pydantic import BaseModel
from typing import List, Optional

class ExecuteRequest(BaseModel):
    dataset: str
    query: Optional[str] = None

class MismatchDetail(BaseModel):
    id: str
    field: str
    source: str
    target: str
    risk: str

class ExecuteResponse(BaseModel):
    totalRows: int
    matches: int
    mismatches: int
    accuracy: float
    mismatchDetails: List[MismatchDetail]

class GenerateQueryRequest(BaseModel):
    prompt: str
    context: Optional[str] = None

class GenerateQueryResponse(BaseModel):
    query: str
    explanation: Optional[str] = None
