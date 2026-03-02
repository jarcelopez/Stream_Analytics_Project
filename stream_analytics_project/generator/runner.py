from __future__ import annotations

import argparse
from pathlib import Path

from stream_analytics_project.config import GeneratorConfig, default_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthetic food-delivery stream generator (Milestone 1)."
    )
    parser.add_argument(
        "--duration-minutes",
        type=int,
        help="Simulation duration in minutes (overrides default).",
    )
    parser.add_argument(
        "--events-per-minute",
        type=int,
        help="Base number of order events per minute (overrides default).",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "avro", "both"],
        help="Output format for generated data.",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        help="Directory to write generated files into.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible simulations.",
    )
    return parser.parse_args()


def build_config_from_args(args: argparse.Namespace) -> GeneratorConfig:
    cfg = default_config()

    if args.duration_minutes is not None:
        cfg.simulation_duration_minutes = args.duration_minutes
    if args.events_per_minute is not None:
        cfg.events_per_minute_base = args.events_per_minute
    if args.output_format is not None:
        cfg.output_format = args.output_format  # type: ignore[assignment]
    if args.output_path is not None:
        cfg.output_path = args.output_path
    if args.seed is not None:
        cfg.random_seed = args.seed

    return cfg


def run_simulation(config: GeneratorConfig) -> None:
    """
    Entry point for Milestone 1 generation.

    This function will be wired up to:
      - create entity universes (zones, restaurants, couriers, customers),
      - generate order and courier events using the configured distributions,
      - inject edge cases,
      - serialise data to JSON and/or AVRO under config.output_path.
    """
    output_dir = Path(config.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # TODO: wire in order and courier generators once implemented.
    # For now, this keeps the CLI runnable without generating data.


def main() -> None:
    args = parse_args()
    config = build_config_from_args(args)
    run_simulation(config)


if __name__ == "__main__":
    main()

