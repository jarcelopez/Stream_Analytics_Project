from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastavro import reader

from stream_analytics.common.config import load_typed_config
from stream_analytics.generator.base_generators import generate_sample_feeds, _apply_edge_cases
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


def test_edge_case_configuration_influences_stream(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Sanity-check that enabling edge-case rates actually changes the generated streams.

    This does not assert exact probabilities, only that:
    - duplicate_rate > 0 leads to more order events than the nominal batch size
    - missing_step_rate > 0 can reduce the number of order events
    - impossible_duration_rate > 0 can create very large delivery_time_seconds
    - courier_offline_rate > 0 increases the number of OFFLINE courier records
    """
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    # Baseline config with all edge-case rates at 0.
    baseline_cfg = tmp_path / "generator_baseline.yaml"
    baseline_cfg.write_text(
        "\n".join(
            [
                "zone_count: 2",
                "restaurant_count: 3",
                "courier_count: 4",
                "demand_level: medium",
                "events_per_second: 10",
                "sample_batch_size_per_feed: 20",
            ]
        ),
        encoding="utf-8",
    )

    edge_cfg = tmp_path / "generator_edge.yaml"
    edge_cfg.write_text(
        "\n".join(
            [
                "zone_count: 2",
                "restaurant_count: 3",
                "courier_count: 4",
                "demand_level: medium",
                "events_per_second: 10",
                "sample_batch_size_per_feed: 20",
                "duplicate_rate: 0.8",
                "missing_step_rate: 0.2",
                "impossible_duration_rate: 0.9",
                "courier_offline_rate: 0.9",
            ]
        ),
        encoding="utf-8",
    )

    from stream_analytics.generator.config_models import GeneratorConfig
    from stream_analytics.common.config import load_typed_config

    # Baseline run
    baseline_config: GeneratorConfig = load_typed_config(
        relative_yaml_path=str(baseline_cfg.name),
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )
    baseline_output = tmp_path / "baseline_samples"
    generate_sample_feeds(config=baseline_config, base_output_dir=str(baseline_output))

    baseline_order_json = baseline_output / "order_events" / "json" / "sample.jsonl"
    baseline_courier_json = baseline_output / "courier_status" / "json" / "sample.jsonl"

    baseline_orders = [
        json.loads(line)
        for line in baseline_order_json.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    baseline_couriers = [
        json.loads(line)
        for line in baseline_courier_json.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # Edge-case heavy run
    edge_config: GeneratorConfig = load_typed_config(
        relative_yaml_path=str(edge_cfg.name),
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )
    edge_output = tmp_path / "edge_samples"
    generate_sample_feeds(config=edge_config, base_output_dir=str(edge_output))

    edge_order_json = edge_output / "order_events" / "json" / "sample.jsonl"
    edge_courier_json = edge_output / "courier_status" / "json" / "sample.jsonl"

    edge_orders = [
        json.loads(line)
        for line in edge_order_json.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edge_couriers = [
        json.loads(line)
        for line in edge_courier_json.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # Duplicate rate should increase order event count.
    assert len(edge_orders) > len(baseline_orders)

    # Some delivery_time_seconds should be unrealistically large in edge run.
    large_durations = [
        rec["delivery_time_seconds"]
        for rec in edge_orders
        if rec.get("delivery_time_seconds") is not None
        and rec["delivery_time_seconds"] > 4 * 60 * 60  # > 4 hours
    ]
    assert large_durations, "Expected some inflated delivery_time_seconds for impossible durations"

    # OFFLINE statuses should be more common in edge run.
    baseline_offline = sum(1 for rec in baseline_couriers if rec["status"] == "OFFLINE")
    edge_offline = sum(1 for rec in edge_couriers if rec["status"] == "OFFLINE")
    assert edge_offline >= baseline_offline


def test_debug_sample_runs_are_reproducible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Debug-mode sample generation should be reproducible enough for teaching/demo
    scenarios when using the same configuration and debug seed.
    """
    from datetime import datetime, timezone

    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    # Fix "now" so time-based fields do not introduce differences between runs.
    from stream_analytics.generator import entities as entities_mod

    fixed_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(entities_mod, "_now", lambda: fixed_now)

    # Write a small config; edge-case rates can stay at defaults for this check.
    config_yaml = _write_minimal_config(tmp_path)

    from stream_analytics.common.config import load_typed_config
    from stream_analytics.generator.config_models import GeneratorConfig
    from stream_analytics.generator.entities import seed_for_debug

    config: GeneratorConfig = load_typed_config(
        relative_yaml_path=str(config_yaml.name),
        model_type=GeneratorConfig,
        env_prefix="GENERATOR_",
    )

    output_dir_1 = tmp_path / "debug_run_1"
    output_dir_2 = tmp_path / "debug_run_2"

    # First debug-style run.
    seed_for_debug(42)
    generate_sample_feeds(config=config, base_output_dir=str(output_dir_1))

    # Second debug-style run with the same seed and config.
    seed_for_debug(42)
    generate_sample_feeds(config=config, base_output_dir=str(output_dir_2))

    def _load_records(base_dir: Path) -> tuple[list[dict], list[dict]]:
        order_json = base_dir / "order_events" / "json" / "sample.jsonl"
        courier_json = base_dir / "courier_status" / "json" / "sample.jsonl"

        orders = [
            json.loads(line)
            for line in order_json.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        couriers = [
            json.loads(line)
            for line in courier_json.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return orders, couriers

    orders_1, couriers_1 = _load_records(output_dir_1)
    orders_2, couriers_2 = _load_records(output_dir_2)

    assert orders_1 == orders_2
    assert couriers_1 == couriers_2


def test_late_event_rate_shifts_event_times() -> None:
    """
    Non-zero late_event_rate should result in some events having an earlier event_time,
    implemented as a fixed backwards shift.
    """
    base_ts = 1_700_000_000_000_000
    order_events = [{"event_time": base_ts, "status": "CREATED"} for _ in range(10)]
    courier_events = [{"event_time": base_ts, "status": "ONLINE"} for _ in range(5)]

    config = GeneratorConfig(late_event_rate=0.5)

    updated_orders, updated_couriers, edge_counts = _apply_edge_cases(
        order_events=order_events,
        courier_events=courier_events,
        config=config,
    )

    all_times = [rec["event_time"] for rec in updated_orders + updated_couriers]
    assert edge_counts["late_event_count"] > 0
    assert min(all_times) < max(all_times)


def test_missing_step_rate_drops_some_order_events() -> None:
    """
    Non-zero missing_step_rate should drop a subset of order events, but never all.
    """
    order_events = [{"event_time": 1, "status": "CREATED"} for _ in range(100)]
    courier_events: list[dict] = []

    config = GeneratorConfig(missing_step_rate=0.5)

    updated_orders, _updated_couriers, edge_counts = _apply_edge_cases(
        order_events=order_events,
        courier_events=courier_events,
        config=config,
    )

    assert edge_counts["missing_step_drop_count"] > 0
    assert 0 < edge_counts["missing_step_drop_count"] < len(order_events)
    assert len(updated_orders) == len(order_events) - edge_counts["missing_step_drop_count"]


