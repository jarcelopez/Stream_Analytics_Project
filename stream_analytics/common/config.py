from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Type, TypeVar

import yaml
from pydantic import ValidationError

from stream_analytics.common.logging_utils import log_error


T = TypeVar("T")


def _project_root() -> Path:
    """
    Best-effort resolution of the project root directory.

    Assumes this file lives under `stream_analytics/common/`.

    Tests can override this via the PYTEST_PROJECT_ROOT_OVERRIDE environment
    variable so that configuration loading can be exercised in isolation.
    """
    override = os.environ.get("PYTEST_PROJECT_ROOT_OVERRIDE")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML config not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at root of YAML file {path}, got {type(data).__name__}")
    return data


def _apply_env_overrides(raw: Dict[str, Any], env_prefix: str) -> Dict[str, Any]:
    """
    Apply environment variable overrides using a simple flat mapping:

    - For key `zone_count`, look for `GENERATOR_ZONE_COUNT` (if prefix is `GENERATOR_`).
    - Environment variables are parsed as strings; type conversion is left to Pydantic.
    """
    result: Dict[str, Any] = dict(raw)
    upper_prefix = env_prefix.upper()

    # First, override any existing keys present in the YAML config.
    for key in list(result.keys()):
        env_key = f"{upper_prefix}{key.upper()}"
        if env_key in os.environ:
            result[key] = os.environ[env_key]

    # Then, allow environment variables to introduce additional keys that are
    # not present in the YAML file (for example EVENTS_PER_SECOND in tests).
    # This lets env-only settings participate in configuration while still
    # leaving validation and field selection to the Pydantic model.
    for env_key, env_value in os.environ.items():
        if not env_key.startswith(upper_prefix):
            continue
        # Strip the prefix and convert the remainder to snake_case-style lower.
        # For keys like GENERATOR_EVENTS_PER_SECOND this produces
        # "events_per_second", which matches our config fields.
        suffix = env_key[len(upper_prefix) :]
        if not suffix:
            continue
        derived_key = suffix.lower()
        if derived_key not in result:
            result[derived_key] = env_value

    return result


def load_typed_config(
    *,
    relative_yaml_path: str,
    model_type: Type[T],
    env_prefix: str,
) -> T:
    """
    Load a YAML config file from the project `config/` directory,
    apply environment-variable overrides, and parse into a Pydantic model.
    """
    root = _project_root()
    yaml_path = root / relative_yaml_path

    raw = load_yaml(yaml_path)
    merged = _apply_env_overrides(raw, env_prefix=env_prefix)

    try:
        return model_type.model_validate(merged)  # type: ignore[attr-defined]
    except ValidationError as exc:
        # Emit a structured error with per-field reason codes.
        errors = []
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err.get("loc", []))
            errors.append(
                {
                    "field": field,
                    "reason": err.get("msg", "invalid value"),
                    "reason_code": "invalid_value",
                    "type": err.get("type", "value_error"),
                }
            )

        log_error(
            component="generator_config",
            message="Invalid generator configuration",
            details={"errors": errors, "config_path": str(yaml_path)},
        )
        raise

