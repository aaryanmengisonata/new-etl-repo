from typing import Dict

from pydantic import BaseModel, Field


class LayerConfig(BaseModel):
    lakehouse: str = ""
    endpoint: str = ""


class EnvironmentConfig(BaseModel):
    bronze: LayerConfig = Field(default_factory=LayerConfig)
    silver: LayerConfig = Field(default_factory=LayerConfig)
    gold: LayerConfig = Field(default_factory=LayerConfig)


class ConfigUpdate(BaseModel):
    FABRIC_LAYER: str
    FABRIC_ENV: str
    FABRIC_LAKEHOUSE: str
    FABRIC_ENDPOINT: str
    FABRIC_CONFIGS: Dict[str, EnvironmentConfig] = Field(default_factory=dict)
