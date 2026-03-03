from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from pydantic import ValidationError

from stream_analytics.common.config import load_typed_config
from stream_analytics.common.logging_utils import log_error, log_info
from stream_analytics.generator.config_models import GeneratorConfig


def _resolve_config(config_path: str) -> GeneratorConfig:
    return load_typed_config(
        relative_yaml_path=config_path,
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )


def _print_config(config: GeneratorConfig) -> None:
    payload: Dict[str, Any] = {
        "component": "generator",
        "event_type": "resolved_config",
        "config": json.loads(config.model_dump_json()),
    }
    print(json.dumps(payload), file=sys.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generator CLI entrypoint – loads GeneratorConfig and (for Story 1.1) prints the resolved configuration.",
    )
    parser.add_argument(
        "--config-path",
        default="config/generator.yaml",
        help="Relative path to generator YAML configuration (default: config/generator.yaml)",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print the resolved configuration and exit without generating events.",
    )

    args = parser.parse_args(argv)

    try:
        config = _resolve_config(config_path=args.config_path)
    except ValidationError:
        # Validation errors are already logged by the shared config loader
        # with component="generator_config" and structured per-field details.
        return 1
    except FileNotFoundError as exc:  # pragma: no cover - simple configuration error
        log_error(
            component="generator_cli",
            message="Generator configuration file not found",
            details={"error": str(exc), "config_path": args.config_path},
        )
        return 1
    except Exception as exc:  # pragma: no cover - unexpected failure path
        log_error(
            component="generator_cli",
            message="Unexpected error while loading generator configuration",
            details={"error": str(exc), "config_path": args.config_path},
        )
        return 1

    log_info(
        component="generator_cli",
        message="Loaded generator configuration",
        details={
            "zone_count": config.zone_count,
            "restaurant_count": config.restaurant_count,
            "courier_count": config.courier_count,
            "demand_level": config.demand_level,
            "events_per_second": config.events_per_second,
            "debug_mode_max_events_per_second": config.debug_mode_max_events_per_second,
            "debug_mode_max_entity_count": config.debug_mode_max_entity_count,
            "sample_batch_size_per_feed": config.sample_batch_size_per_feed,
        },
    )

    if args.print_config:
        _print_config(config)
        return 0

    # Story 1.1 stops at configuration; later stories will call into
    # generator core modules to actually emit events.
    log_info(
        component="generator_cli",
        message="Configuration resolved; event generation is implemented in later stories.",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

