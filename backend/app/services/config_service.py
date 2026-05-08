from __future__ import annotations

from configparser import ConfigParser
from copy import deepcopy
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "master.properties"
LAYER_SECTION_MAP = {
    "bronze": "FABRIC_BRONZE",
    "silver": "FABRIC_SILVER",
    "gold": "FABRIC_GOLD",
}
ENVIRONMENT_MAP = {
    "dev": "DEV",
    "qa": "QAT",
    "test": "QAT",
    "prod": "PROD",
}
UI_ENVIRONMENT_MAP = {
    "DEV": "dev",
    "QAT": "qa",
    "PROD": "prod",
}
ENV_KEY_MAP = {
    "dev": "DEV",
    "qa": "QAT",
    "prod": "PROD",
}
DEFAULT_ENV_CONFIGS = {
    "dev": {
        "bronze": {"lakehouse": "", "endpoint": ""},
        "silver": {"lakehouse": "", "endpoint": ""},
        "gold": {"lakehouse": "", "endpoint": ""},
    },
    "qa": {
        "bronze": {"lakehouse": "", "endpoint": ""},
        "silver": {"lakehouse": "", "endpoint": ""},
        "gold": {"lakehouse": "", "endpoint": ""},
    },
    "prod": {
        "bronze": {"lakehouse": "", "endpoint": ""},
        "silver": {"lakehouse": "", "endpoint": ""},
        "gold": {"lakehouse": "", "endpoint": ""},
    },
}


def _load_parser() -> ConfigParser:
    parser = ConfigParser()
    parser.optionxform = str
    parser.read(CONFIG_PATH)
    return parser


def _get_active_layer(parser: ConfigParser) -> str:
    active_layer = parser.get("DEFAULT", "ACTIVE_FABRIC_LAYER", fallback="BRONZE")
    return active_layer.strip().lower()


def _get_layer_keys(layer: str) -> tuple[str, str]:
    normalized_layer = layer.lower()
    section = LAYER_SECTION_MAP.get(normalized_layer, "FABRIC_BRONZE")
    prefix = normalized_layer.upper()
    return section, prefix


def _get_layer_value(parser: ConfigParser, env: str, layer: str) -> dict[str, str]:
    section, prefix = _get_layer_keys(layer)
    env_prefix = ENV_KEY_MAP[env]
    return {
        "lakehouse": parser.get(
            section,
            f"{env_prefix}_{prefix}_LAKEHOUSE_NAME",
            fallback=parser.get(section, f"{prefix}_LAKEHOUSE_NAME", fallback=""),
        ),
        "endpoint": parser.get(
            section,
            f"{env_prefix}_{prefix}_SQL_ENDPOINT",
            fallback=parser.get(section, f"{prefix}_SQL_ENDPOINT", fallback=""),
        ),
    }


def _build_env_configs(parser: ConfigParser) -> dict[str, dict[str, dict[str, str]]]:
    env_configs = deepcopy(DEFAULT_ENV_CONFIGS)
    for env in env_configs:
        for layer in env_configs[env]:
            env_configs[env][layer] = _get_layer_value(parser, env, layer)
    return env_configs


def _sync_active_environment_values(parser: ConfigParser, env: str) -> None:
    env_prefix = ENV_KEY_MAP[env]
    for layer in ("bronze", "silver", "gold"):
        section, prefix = _get_layer_keys(layer)
        if not parser.has_section(section):
            parser.add_section(section)

        parser[section][f"{prefix}_LAKEHOUSE_NAME"] = parser.get(
            section,
            f"{env_prefix}_{prefix}_LAKEHOUSE_NAME",
            fallback=parser.get(section, f"{prefix}_LAKEHOUSE_NAME", fallback=""),
        )
        parser[section][f"{prefix}_SQL_ENDPOINT"] = parser.get(
            section,
            f"{env_prefix}_{prefix}_SQL_ENDPOINT",
            fallback=parser.get(section, f"{prefix}_SQL_ENDPOINT", fallback=""),
        )


def load_config() -> dict[str, object]:
    parser = _load_parser()
    layer = _get_active_layer(parser)
    environment = parser.get("DEFAULT", "ENVIRONMENT", fallback="DEV").strip().upper()
    ui_environment = UI_ENVIRONMENT_MAP.get(environment, environment.lower())
    env_configs = _build_env_configs(parser)
    selected = env_configs[ui_environment][layer]

    return {
        "FABRIC_LAYER": layer,
        "FABRIC_ENV": ui_environment,
        "FABRIC_LAKEHOUSE": selected["lakehouse"],
        "FABRIC_ENDPOINT": selected["endpoint"],
        "FABRIC_CONFIGS": env_configs,
    }


def save_config(payload) -> dict[str, object]:
    parser = _load_parser()
    layer = payload.FABRIC_LAYER.lower()
    environment = ENVIRONMENT_MAP.get(payload.FABRIC_ENV.lower(), payload.FABRIC_ENV.upper())
    ui_environment = UI_ENVIRONMENT_MAP.get(environment, environment.lower())
    env_configs = _build_env_configs(parser)

    incoming_configs = {}
    for env_name, env_value in payload.FABRIC_CONFIGS.items():
        if hasattr(env_value, "model_dump"):
            incoming_configs[env_name] = env_value.model_dump()
        else:
            incoming_configs[env_name] = env_value

    for env_name in ("dev", "qa", "prod"):
        for layer_name in ("bronze", "silver", "gold"):
            layer_config = incoming_configs.get(env_name, {}).get(layer_name, {})
            if layer_config:
                env_configs[env_name][layer_name] = {
                    "lakehouse": layer_config.get("lakehouse", ""),
                    "endpoint": layer_config.get("endpoint", ""),
                }

    env_configs[ui_environment][layer] = {
        "lakehouse": payload.FABRIC_LAKEHOUSE,
        "endpoint": payload.FABRIC_ENDPOINT,
    }

    parser["DEFAULT"]["ENVIRONMENT"] = environment
    parser["DEFAULT"]["ACTIVE_FABRIC_LAYER"] = layer.upper()

    for env_name in ("dev", "qa", "prod"):
        env_prefix = ENV_KEY_MAP[env_name]
        for layer_name in ("bronze", "silver", "gold"):
            section, prefix = _get_layer_keys(layer_name)
            if not parser.has_section(section):
                parser.add_section(section)

            parser[section][f"{env_prefix}_{prefix}_LAKEHOUSE_NAME"] = env_configs[env_name][layer_name]["lakehouse"]
            parser[section][f"{env_prefix}_{prefix}_SQL_ENDPOINT"] = env_configs[env_name][layer_name]["endpoint"]

    _sync_active_environment_values(parser, ui_environment)

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)

    return {
        "message": "Configuration saved successfully",
        "config": {
            "FABRIC_LAYER": layer,
            "FABRIC_ENV": ui_environment,
            "FABRIC_LAKEHOUSE": env_configs[ui_environment][layer]["lakehouse"],
            "FABRIC_ENDPOINT": env_configs[ui_environment][layer]["endpoint"],
            "FABRIC_CONFIGS": env_configs,
        },
        "updated_file": str(CONFIG_PATH),
    }
