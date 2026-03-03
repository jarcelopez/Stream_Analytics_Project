from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastavro import reader

from stream_analytics.common.config import load_typed_config
from stream_analytics.generator.base_generators import generate_sample_feeds
from stream_analytics.generator.config_models import GeneratorConfig


def _write_minimal_config(tmp_path: Path) -> Path:
    config_yaml = tmp_path / "generator.yaml"
    config_yaml.write_text(
        "\n".join(
            [
                "zone_count: 2",
                "restaurant_count: 3",
                "courier_count: 4",
                "demand_level: medium",
                "events_per_second: 10",
                "sample_batch_size_per_feed: 5",
            ]
        ),
        encoding="utf-8",
    )
    return config_yaml


def test_generate_sample_feeds_creates_both_feeds_in_json_and_avro(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: point project root at tmp_path and write minimal config.
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))
    config_yaml = _write_minimal_config(tmp_path)

    config: GeneratorConfig = load_typed_config(
        relative_yaml_path=str(config_yaml.name),
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )

    output_dir = tmp_path / "samples"

    # Act
    generate_sample_feeds(config=config, base_output_dir=str(output_dir))

    # Assert: JSON files exist and are line-delimited JSON with correct feed_type separation.
    order_json = output_dir / "order_events" / "json" / "sample.jsonl"
    courier_json = output_dir / "courier_status" / "json" / "sample.jsonl"

    assert order_json.is_file()
    assert courier_json.is_file()

    order_records = [json.loads(line) for line in order_json.read_text(encoding="utf-8").splitlines() if line.strip()]
    courier_records = [json.loads(line) for line in courier_json.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert order_records, "Expected at least one order_events record"
    assert courier_records, "Expected at least one courier_status record"

    assert all(rec["feed_type"] == "order_events" for rec in order_records)
    assert all(rec["feed_type"] == "courier_status" for rec in courier_records)

    # Assert: AVRO files exist and can be decoded via fastavro.
    order_avro = output_dir / "order_events" / "avro" / "sample.avro"
    courier_avro = output_dir / "courier_status" / "avro" / "sample.avro"

    assert order_avro.is_file()
    assert courier_avro.is_file()

    with order_avro.open("rb") as f:
        order_reader = list(reader(f))
    with courier_avro.open("rb") as f:
        courier_reader = list(reader(f))

    assert order_reader, "Expected at least one AVRO order_events record"
    assert courier_reader, "Expected at least one AVRO courier_status record"

    # Basic schema consistency checks
    for rec in order_reader:
        assert rec["feed_type"] == "order_events"
        assert "order_id" in rec and "event_time" in rec and "status" in rec
        assert isinstance(rec["order_id"], str)
        # fastavro returns Python datetime for timestamp-micros logical type
        from datetime import datetime

        assert isinstance(rec["event_time"], datetime)

    for rec in courier_reader:
        assert rec["feed_type"] == "courier_status"
        assert "courier_id" in rec and "event_time" in rec and "status" in rec
        assert isinstance(rec["courier_id"], str)
        from datetime import datetime

        assert isinstance(rec["event_time"], datetime)

    # JSON records should mirror the AVRO-required fields and basic types.
    required_order_fields = {
        "order_id",
        "restaurant_id",
        "courier_id",
        "zone_id",
        "event_time",
        "status",
        "feed_type",
    }
    expected_order_fields = required_order_fields | {"total_amount", "delivery_time_seconds"}
    for rec in order_records:
        assert set(rec.keys()) == expected_order_fields
        assert isinstance(rec["order_id"], str)
        assert isinstance(rec["restaurant_id"], str)
        assert isinstance(rec["courier_id"], str)
        assert isinstance(rec["zone_id"], str)
        assert isinstance(rec["event_time"], int)
        assert isinstance(rec["status"], str)
        assert rec["feed_type"] == "order_events"

    required_courier_fields = {"courier_id", "zone_id", "event_time", "status", "feed_type"}
    expected_courier_fields = required_courier_fields | {"active_order_id"}
    for rec in courier_records:
        assert set(rec.keys()) == expected_courier_fields
        assert isinstance(rec["courier_id"], str)
        assert isinstance(rec["zone_id"], str)
        assert isinstance(rec["event_time"], int)
        assert isinstance(rec["status"], str)
        assert rec["feed_type"] == "courier_status"


