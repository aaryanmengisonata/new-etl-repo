from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.config import router as config_router
from app.routers.test_cases import router as test_cases_router


app = FastAPI(title="ETL Testing Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router)
app.include_router(test_cases_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
