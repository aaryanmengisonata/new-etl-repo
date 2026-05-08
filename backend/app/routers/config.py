from fastapi import APIRouter

from app.models.config import ConfigUpdate
from app.services.config_service import load_config, save_config


router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def get_config():
    return load_config()


@router.post("/config")
def update_config(payload: ConfigUpdate):
    return save_config(payload)
