from pydantic import BaseModel


class TestCaseSummary(BaseModel):
    test_id: str
    functionality: str
    sql_id: str
    expected_condition: str
    enabled: str
    description: str
    source_file: str
    dataset: str
