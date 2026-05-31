from fastapi import APIRouter

from app.models.config import (
    ConfigUpdate, DbConfigUpdate, DbConnectionConfig,
    PipelineConfig, ApiSentryConfig, IntegrationConfig,
    TestingConfig, ReportingConfig,
)
from app.services.config_service import (
    load_config, save_config,
    load_db_config, save_db_config,
    load_pipeline_config, save_pipeline_config,
    load_api_config, save_api_config,
    load_integration_config, save_integration_config,
    load_testing_config, save_testing_config,
    load_reporting_config, save_reporting_config,
)


router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def get_config():
    return load_config()


@router.post("/config")
def update_config(payload: ConfigUpdate):
    return save_config(payload)

@router.get("/config/db")
def get_db_config():
    return load_db_config()

@router.post("/config/db")
def update_db_config(payload: DbConnectionConfig):
    return save_db_config(payload)

@router.get("/config/pipeline")
def get_pipeline_config():
    return load_pipeline_config()

@router.post("/config/pipeline")
def update_pipeline_config(payload: PipelineConfig):
    return save_pipeline_config(payload)

@router.get("/config/api-sentry")
def get_api_sentry_config():
    return load_api_config()

@router.post("/config/api-sentry")
def update_api_sentry_config(payload: ApiSentryConfig):
    return save_api_config(payload)

@router.get("/config/integration")
def get_integration_config():
    return load_integration_config()

@router.post("/config/integration")
def update_integration_config(payload: IntegrationConfig):
    return save_integration_config(payload)

@router.get("/config/testing")
def get_testing_config():
    return load_testing_config()

@router.post("/config/testing")
def update_testing_config(payload: TestingConfig):
    return save_testing_config(payload)

@router.get("/config/reporting")
def get_reporting_config():
    return load_reporting_config()

@router.post("/config/reporting")
def update_reporting_config(payload: ReportingConfig):
    return save_reporting_config(payload)
