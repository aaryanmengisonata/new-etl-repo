from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.config import router as config_router
from app.routers.test_cases import router as test_cases_router
from app.routers.execution import router as execution_router
from app.routers.interactive_testing import router as interactive_testing_router
from app.routers.reports import router as reports_router
from app.routers.pipeline_auditor import router as pipeline_auditor_router
from app.routers.integration_sentry import router as integration_sentry_router

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
app.include_router(interactive_testing_router)
app.include_router(reports_router)
app.include_router(pipeline_auditor_router)
app.include_router(integration_sentry_router)



@app.get("/health")
def health_check():
    return {"status": "ok"}


from fastapi import Query
from fastapi.responses import StreamingResponse
import subprocess
import asyncio
import json
from typing import Optional, List
from pathlib import Path

# Track running test execution processes
active_processes = {}

@app.get("/api/suites", response_model=List[str])
def get_suites():
    """
    Returns the list of available test suites for the ETL engine.
    """
    test_dir = Path("tests/etl")
    if not test_dir.exists():
        return []
    return [f.name for f in test_dir.glob("test_*.py") if f.is_file()]

@app.post("/api/stop-test/{engine}")
def stop_test(engine: str):
    """
    Stops a running test execution.
    """
    process = active_processes.get(engine)
    if process:
        try:
            process.terminate()
            return {"status": "success", "message": f"Stopped {engine} execution"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop: {str(e)}"}
    return {"status": "success", "message": "No process running"}

@app.get("/stream-logs/{engine}")
async def stream_logs(engine: str, suite: Optional[str] = None):
    """
    Streams test logs via SSE in real-time.
    """
    engine_map = {
        "etl": "etl",
        "api": "api",
        "db": "db",
        "integration": "integration"
    }
    dir_name = engine_map.get(engine)
    if not dir_name:
        async def err_gen():
            yield f"event: log\ndata: {json.dumps({'msg': '[ERROR] Invalid engine selected.'})}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")
        
    test_path = f"tests/{dir_name}"
    if suite:
        test_path = f"tests/{dir_name}/{suite}"
        
    async def log_generator():
        cmd = [".\\venv\\Scripts\\python", "-m", "pytest", test_path, "-v", "--color=no"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        active_processes[engine] = process
        
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode('utf-8', errors='ignore').rstrip('\r\n')
                yield f"event: log\ndata: {json.dumps({'msg': decoded_line})}\n\n"
                
            await process.wait()
        except asyncio.CancelledError:
            try:
                process.terminate()
            except Exception:
                pass
            raise
        finally:
            active_processes.pop(engine, None)
            yield "event: done\ndata: {}\n\n"
            
    return StreamingResponse(log_generator(), media_type="text/event-stream")

