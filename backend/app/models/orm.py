from sqlalchemy import Column, Integer, String, Text, Boolean
from app.database import Base

class TestCaseDB(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String, index=True)
    functionality = Column(String)
    sql_id = Column(String)
    expected_condition = Column(String)
    enabled = Column(String)
    description = Column(Text)
    source_file = Column(String)
    dataset = Column(String, index=True)
