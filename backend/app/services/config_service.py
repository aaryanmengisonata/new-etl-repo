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

def load_db_config() -> dict[str, str]:
    parser = _load_parser()
    section = "DATABASE"
    if not parser.has_section(section):
        return {
            "engine": "sqlite",
            "host": "localhost",
            "port": "5432",
            "db_name": "etl_test.db",
            "username": "",
            "password": "",
        }
    return {
        "engine": parser.get(section, "ENGINE", fallback="sqlite"),
        "host": parser.get(section, "HOST", fallback="localhost"),
        "port": parser.get(section, "PORT", fallback="5432"),
        "db_name": parser.get(section, "DB_NAME", fallback="etl_test.db"),
        "username": parser.get(section, "USERNAME", fallback=""),
        "password": parser.get(section, "PASSWORD", fallback=""),
    }

def save_db_config(payload) -> dict[str, object]:
    parser = _load_parser()
    section = "DATABASE"
    if not parser.has_section(section):
        parser.add_section(section)
        
    parser[section]["ENGINE"] = payload.engine
    parser[section]["HOST"] = payload.host
    parser[section]["PORT"] = payload.port
    parser[section]["DB_NAME"] = payload.db_name
    parser[section]["USERNAME"] = payload.username
    parser[section]["PASSWORD"] = payload.password
    
    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)
        
    return {
        "message": "Database configuration saved successfully",
        "config": load_db_config()
    }


def load_pipeline_config() -> dict[str, object]:
    parser = _load_parser()
    section = "PIPELINE_AUDITOR"
    if not parser.has_section(section):
        return {
            "default_row_limit": 10000,
            "default_chunk_size": 2000,
            "default_query_timeout": 30,
            "default_source_db": "test_audit_src_test.db",
            "default_target_db": "test_audit_tgt_test.db",
        }
    return {
        "default_row_limit": parser.getint(section, "DEFAULT_ROW_LIMIT", fallback=10000),
        "default_chunk_size": parser.getint(section, "DEFAULT_CHUNK_SIZE", fallback=2000),
        "default_query_timeout": parser.getint(section, "DEFAULT_QUERY_TIMEOUT", fallback=30),
        "default_source_db": parser.get(section, "DEFAULT_SOURCE_DB", fallback="test_audit_src_test.db"),
        "default_target_db": parser.get(section, "DEFAULT_TARGET_DB", fallback="test_audit_tgt_test.db"),
    }


def save_pipeline_config(payload) -> dict[str, object]:
    parser = _load_parser()
    section = "PIPELINE_AUDITOR"
    if not parser.has_section(section):
        parser.add_section(section)
        
    parser[section]["DEFAULT_ROW_LIMIT"] = str(payload.default_row_limit)
    parser[section]["DEFAULT_CHUNK_SIZE"] = str(payload.default_chunk_size)
    parser[section]["DEFAULT_QUERY_TIMEOUT"] = str(payload.default_query_timeout)
    parser[section]["DEFAULT_SOURCE_DB"] = payload.default_source_db
    parser[section]["DEFAULT_TARGET_DB"] = payload.default_target_db
    
    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)
        
    return {
        "message": "Pipeline auditor configuration saved successfully",
        "config": load_pipeline_config()
    }


def load_api_config() -> dict[str, object]:
    parser = _load_parser()
    section = "API"
    if not parser.has_section(section):
        return {
            "base_url": "https://fakestoreapi.com",
            "timeout": 30,
            "ssl_verify": False,
        }
    return {
        "base_url": parser.get(section, "API_BASE_URL", fallback="https://fakestoreapi.com"),
        "timeout": parser.getint(section, "API_TIMEOUT", fallback=30),
        "ssl_verify": parser.getboolean(section, "SSL_VERIFY", fallback=False),
    }


def save_api_config(payload) -> dict[str, object]:
    parser = _load_parser()
    section = "API"
    if not parser.has_section(section):
        parser.add_section(section)

    parser[section]["API_BASE_URL"] = payload.base_url
    parser[section]["API_TIMEOUT"] = str(payload.timeout)
    parser[section]["SSL_VERIFY"] = str(payload.ssl_verify)

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)

    return {
        "message": "API Sentry configuration saved successfully",
        "config": load_api_config(),
    }


def load_integration_config() -> dict[str, object]:
    parser = _load_parser()
    section = "INTEGRATION"
    if not parser.has_section(section):
        return {
            "source_db": "test_audit_src_test.db",
            "target_db": "test_audit_tgt_test.db",
            "key_column": "id",
            "reconciliation_type": "data_diff",
        }
    return {
        "source_db": parser.get(section, "SOURCE_DB", fallback="test_audit_src_test.db"),
        "target_db": parser.get(section, "TARGET_DB", fallback="test_audit_tgt_test.db"),
        "key_column": parser.get(section, "KEY_COLUMN", fallback="id"),
        "reconciliation_type": parser.get(section, "RECONCILIATION_TYPE", fallback="data_diff"),
    }


def save_integration_config(payload) -> dict[str, object]:
    parser = _load_parser()
    section = "INTEGRATION"
    if not parser.has_section(section):
        parser.add_section(section)

    parser[section]["SOURCE_DB"] = payload.source_db
    parser[section]["TARGET_DB"] = payload.target_db
    parser[section]["KEY_COLUMN"] = payload.key_column
    parser[section]["RECONCILIATION_TYPE"] = payload.reconciliation_type

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)

    return {
        "message": "Integration Sentry configuration saved successfully",
        "config": load_integration_config(),
    }


def load_testing_config() -> dict[str, object]:
    parser = _load_parser()
    section = "TESTING"
    if not parser.has_section(section):
        return {
            "csv_file": "test_cases.csv",
            "sql_dir": "sql",
            "report_dir": "reports",
            "enable_parallel": False,
            "max_workers": 4,
        }
    return {
        "csv_file": parser.get(section, "CSV_FILE", fallback="test_cases.csv"),
        "sql_dir": parser.get(section, "SQL_DIR", fallback="sql"),
        "report_dir": parser.get(section, "REPORT_DIR", fallback="reports"),
        "enable_parallel": parser.getboolean(section, "ENABLE_PARALLEL", fallback=False),
        "max_workers": parser.getint(section, "MAX_WORKERS", fallback=4),
    }


def save_testing_config(payload) -> dict[str, object]:
    parser = _load_parser()
    section = "TESTING"
    if not parser.has_section(section):
        parser.add_section(section)

    parser[section]["CSV_FILE"] = payload.csv_file
    parser[section]["SQL_DIR"] = payload.sql_dir
    parser[section]["REPORT_DIR"] = payload.report_dir
    parser[section]["ENABLE_PARALLEL"] = str(payload.enable_parallel)
    parser[section]["MAX_WORKERS"] = str(payload.max_workers)

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)

    return {
        "message": "Testing configuration saved successfully",
        "config": load_testing_config(),
    }


def load_reporting_config() -> dict[str, object]:
    parser = _load_parser()
    section = "REPORTING"
    if not parser.has_section(section):
        return {
            "allure_results": "reports/allure-results",
            "xml_results": "reports/xml-results",
            "generate_xml": True,
            "generate_html": True,
        }
    return {
        "allure_results": parser.get(section, "ALLURE_RESULTS", fallback="reports/allure-results"),
        "xml_results": parser.get(section, "XML_RESULTS", fallback="reports/xml-results"),
        "generate_xml": parser.getboolean(section, "GENERATE_XML", fallback=True),
        "generate_html": parser.getboolean(section, "GENERATE_HTML", fallback=True),
    }


def save_reporting_config(payload) -> dict[str, object]:
    parser = _load_parser()
    section = "REPORTING"
    if not parser.has_section(section):
        parser.add_section(section)

    parser[section]["ALLURE_RESULTS"] = payload.allure_results
    parser[section]["XML_RESULTS"] = payload.xml_results
    parser[section]["GENERATE_XML"] = str(payload.generate_xml)
    parser[section]["GENERATE_HTML"] = str(payload.generate_html)

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)

    return {
        "message": "Reporting configuration saved successfully",
        "config": load_reporting_config(),
    }

