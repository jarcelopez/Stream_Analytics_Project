from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

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

    formats = set(config.output_formats)

    if "json" in formats:
        write_json_events(outputs.json_order_path, order_list)
        write_json_events(outputs.json_courier_path, courier_list)

    if "avro" in formats:
        write_avro_events(outputs.avro_order_path, order_list, outputs.order_schema_path)
        write_avro_events(outputs.avro_courier_path, courier_list, outputs.courier_schema_path)


