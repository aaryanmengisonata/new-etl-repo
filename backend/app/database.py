import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/etl_test")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_dynamic_engine():
    from app.services.config_service import load_db_config
    db_cfg = load_db_config()
    engine_type = db_cfg.get("engine", "sqlite").lower()
    db_name = db_cfg.get("db_name", "etl_test.db")
    
    # Map common driver/dialect names
    if engine_type == "postgres":
        engine_type = "postgresql"
    elif engine_type in ("sqlserver", "mssql"):
        engine_type = "mssql+pyodbc"
        
    if engine_type == "sqlite":
        return create_engine(f"sqlite:///{db_name}")
    else:
        host = db_cfg.get("host", "localhost")
        port = db_cfg.get("port", "5432")
        username = db_cfg.get("username", "")
        password = db_cfg.get("password", "")
        
        if username:
            if password:
                url = f"{engine_type}://{username}:{password}@{host}:{port}/{db_name}"
            else:
                url = f"{engine_type}://{username}@{host}:{port}/{db_name}"
        else:
            url = f"{engine_type}://{host}:{port}/{db_name}"
            
        return create_engine(url)

