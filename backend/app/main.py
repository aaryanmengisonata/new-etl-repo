from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.config import router as config_router
from app.routers.test_cases import router as test_cases_router
from app.routers.execution import router as execution_router

from contextlib import asynccontextmanager
from app.database import engine, Base, SessionLocal
from app.services.test_case_service import import_csv_to_db_if_empty

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    
    # Import CSV data if DB is empty
    db = SessionLocal()
    try:
        import_csv_to_db_if_empty(db)
    finally:
        db.close()
    
    yield

app = FastAPI(title="ETL Testing Backend API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router)
app.include_router(test_cases_router)
app.include_router(execution_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
