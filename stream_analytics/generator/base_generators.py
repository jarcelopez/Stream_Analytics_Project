from __future__ import annotations

from dataclasses import dataclass
import random
from pathlib import Path
from typing import Iterable, Mapping, Tuple, List, Dict, Any

from stream_analytics.common.logging_utils import log_info
from stream_analytics.generator.config_models import GeneratorConfig
from stream_analytics.generator.entities import generate_two_feeds_sample
from stream_analytics.generator.serialization import write_avro_events, write_json_events


@dataclass
class OutputConfig:
    json_order_path: Path
    json_courier_path: Path
    avro_order_path: Path
    avro_courier_path: Path
    order_schema_path: Path
    courier_schema_path: Path


def _resolve_output_paths(base_dir: Path) -> OutputConfig:
    json_order = base_dir / "order_events" / "json" / "sample.jsonl"
    json_courier = base_dir / "courier_status" / "json" / "sample.jsonl"

    avro_order = base_dir / "order_events" / "avro" / "sample.avro"
    avro_courier = base_dir / "courier_status" / "avro" / "sample.avro"

    schema_dir = Path(__file__).with_suffix("").parent / "schemas"
    return OutputConfig(
        json_order_path=json_order,
        json_courier_path=json_courier,
        avro_order_path=avro_order,
        avro_courier_path=avro_courier,
        order_schema_path=schema_dir / "order_events.avsc",
        courier_schema_path=schema_dir / "courier_status.avsc",
    )


def generate_sample_feeds(config: GeneratorConfig, base_output_dir: str | None = None) -> None:
    """
    Generate a small batch per feed for validation and samples.

    This function is intentionally limited to the sample/preview behavior
    described in Story 1.2. Larger-scale continuous generation will be
    added by later stories.
    """
    base_dir = Path(base_output_dir or config.output_base_dir).resolve()
    outputs = _resolve_output_paths(base_dir)

    order_events, courier_events = generate_two_feeds_sample(
        zone_count=config.zone_count,
        restaurant_count=config.restaurant_count,
        courier_count=config.courier_count,
        sample_batch_size_per_feed=config.sample_batch_size_per_feed or 100,
    )

    # Materialize iterators so we can write to both JSON and AVRO.
    order_list = list(order_events)
    courier_list = list(courier_events)

    order_list, courier_list, edge_counts = _apply_edge_cases(
        order_events=order_list,
        courier_events=courier_list,
        config=config,
    )

    formats = set(config.output_formats)

    if "json" in formats:
        write_json_events(outputs.json_order_path, order_list)
        write_json_events(outputs.json_courier_path, courier_list)

    if "avro" in formats:
        write_avro_events(outputs.avro_order_path, order_list, outputs.order_schema_path)
        write_avro_events(outputs.avro_courier_path, courier_list, outputs.courier_schema_path)

    # Structured observability hook for Story 1.3.
    log_info(
        component="generator_edge_cases",
        message="Generated sample feeds with edge-case configuration.",
        details={
            "total_order_events": len(order_list),
            "total_courier_events": len(courier_list),
            "late_event_count": edge_counts["late_event_count"],
            "duplicate_event_count": edge_counts["duplicate_event_count"],
            "missing_step_drop_count": edge_counts["missing_step_drop_count"],
            "impossible_duration_count": edge_counts["impossible_duration_count"],
            "courier_offline_toggle_count": edge_counts["courier_offline_toggle_count"],
            "late_event_rate": config.late_event_rate,
            "duplicate_rate": config.duplicate_rate,
            "missing_step_rate": config.missing_step_rate,
            "impossible_duration_rate": config.impossible_duration_rate,
            "courier_offline_rate": config.courier_offline_rate,
        },
    )


def _apply_edge_cases(
    order_events: List[Dict[str, Any]],
    courier_events: List[Dict[str, Any]],
    config: GeneratorConfig,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Apply edge-case behaviors to the already-generated events based on configuration.

    Encoding strategy (JSON + AVRO, no schema changes required for Story 1.3):
    - late_event_rate: shift a subset of events backwards in time, simulating late arrival,
      by subtracting a fixed delay from their event_time.
    - duplicate_rate: duplicate a subset of order events, keeping identifiers the same so
      downstream jobs see true duplicates.
    - missing_step_rate: drop a subset of order events to simulate missing lifecycle steps.
    - impossible_duration_rate: inflate delivery_time_seconds for some delivered orders to
      values far outside the normal range.
    - courier_offline_rate: flip a subset of courier events to OFFLINE status, sometimes
      while they still have an active_order_id.
    """
    # Fast no-op when all edge cases are disabled.
    if (
        config.late_event_rate == 0.0
        and config.duplicate_rate == 0.0
        and config.missing_step_rate == 0.0
        and config.impossible_duration_rate == 0.0
        and config.courier_offline_rate == 0.0
    ):
        return order_events, courier_events, {
            "late_event_count": 0,
            "duplicate_event_count": 0,
            "missing_step_drop_count": 0,
            "impossible_duration_count": 0,
            "courier_offline_toggle_count": 0,
        }

    rng = random.Random(0)
    edge_counts: Dict[str, int] = {
        "late_event_count": 0,
        "duplicate_event_count": 0,
        "missing_step_drop_count": 0,
        "impossible_duration_count": 0,
        "courier_offline_toggle_count": 0,
    }

    # Late / out-of-order events: shift some events back by 10 minutes.
    if config.late_event_rate > 0.0:
        delay_micros = 10 * 60 * 1_000_000
        for rec in order_events + courier_events:
            if rng.random() < config.late_event_rate:
                ts = int(rec.get("event_time", 0))
                rec["event_time"] = ts - delay_micros
                edge_counts["late_event_count"] += 1

    # Duplicates: add extra copies of some order events.
    if config.duplicate_rate > 0.0 and order_events:
        duplicates: List[Dict[str, Any]] = []
        for rec in order_events:
            if rng.random() < config.duplicate_rate:
                duplicates.append(dict(rec))
                edge_counts["duplicate_event_count"] += 1
        order_events = order_events + duplicates

    # Missing steps: drop some order events, but never drop all of them.
    if config.missing_step_rate > 0.0 and order_events:
        kept: List[Dict[str, Any]] = []
        for rec in order_events:
            if rng.random() >= config.missing_step_rate:
                kept.append(rec)
            else:
                edge_counts["missing_step_drop_count"] += 1
        if kept:
            order_events = kept

    # Impossible durations: inflate some delivery times to unrealistic values.
    if config.impossible_duration_rate > 0.0:
        for rec in order_events:
            if rec.get("status") == "DELIVERED" and rec.get("delivery_time_seconds") is not None:
                if rng.random() < config.impossible_duration_rate:
                    rec["delivery_time_seconds"] = float(12 * 60 * 60)  # 12 hours
                    edge_counts["impossible_duration_count"] += 1

    # Courier offline behavior: mark some couriers as OFFLINE, even if they have active orders.
    if config.courier_offline_rate > 0.0 and courier_events:
        for rec in courier_events:
            if rng.random() < config.courier_offline_rate:
                rec["status"] = "OFFLINE"
                edge_counts["courier_offline_toggle_count"] += 1

    return order_events, courier_events, edge_counts


