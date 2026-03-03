from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from pydantic import ValidationError

from stream_analytics.common.config import load_typed_config
from stream_analytics.common.logging_utils import log_error, log_info
from stream_analytics.generator.base_generators import generate_sample_feeds
from stream_analytics.generator.config_models import GeneratorConfig
from stream_analytics.generator.entities import seed_for_debug


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
        description=(
            "Generator CLI entrypoint – loads GeneratorConfig and can either "
            "print the resolved configuration or generate sample feeds."
        ),
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
    parser.add_argument(
        "--sample",
        action="store_true",
        help=(
            "Generate a small sample batch per feed (order_events and courier_status) "
            "in JSON and AVRO formats using the current configuration."
        ),
    )
    parser.add_argument(
        "--debug-sample",
        action="store_true",
        help=(
            "Generate a small, debug-mode sample batch per feed with deterministic "
            "randomness and entity caps for reproducible teaching/demo scenarios."
        ),
    )
    parser.add_argument(
        "--debug-seed",
        type=int,
        default=0,
        help=(
            "Seed used for debug-mode sample generation when --debug-sample is set. "
            "The same seed and configuration will produce reproducible debug runs."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Base directory for generated sample outputs when using --sample. "
            "If omitted, uses output_base_dir from GeneratorConfig."
        ),
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

    if args.sample or args.debug_sample:
        is_debug = bool(args.debug_sample)
        output_dir = args.output_dir or config.output_base_dir

        effective_config = config
        if is_debug:
            # In debug mode, clamp entity-related knobs to stay within documented caps.
            max_entities = config.debug_mode_max_entity_count or config.courier_count
            clamped_zone_count = min(config.zone_count, max_entities)
            clamped_restaurant_count = min(config.restaurant_count, max_entities)
            clamped_courier_count = min(config.courier_count, max_entities)

            effective_config = config.model_copy(
                update={
                    "zone_count": clamped_zone_count,
                    "restaurant_count": clamped_restaurant_count,
                    "courier_count": clamped_courier_count,
                }
            )

            seed_for_debug(args.debug_seed)

        log_info(
            component="generator_cli",
            message="Generating sample feeds for order_events and courier_status.",
            details={
                "output_dir": output_dir,
                "output_formats": effective_config.output_formats,
                "debug_mode": is_debug,
                "debug_seed": args.debug_seed if is_debug else None,
                "zone_count": effective_config.zone_count,
                "restaurant_count": effective_config.restaurant_count,
                "courier_count": effective_config.courier_count,
                "debug_mode_max_events_per_second": config.debug_mode_max_events_per_second,
                "debug_mode_max_entity_count": config.debug_mode_max_entity_count,
            },
        )
        generate_sample_feeds(config=effective_config, base_output_dir=output_dir)
        return 0

    log_info(
        component="generator_cli",
        message="Configuration resolved; no generation mode selected (use --sample or future story modes).",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

