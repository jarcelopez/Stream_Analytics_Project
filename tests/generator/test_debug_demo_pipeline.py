from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream_analytics.generator.cli import main as cli_main


def _load_jsonl(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def test_debug_demo_generates_dual_feeds_small_batches(tmp_path):
    """
    A debug-style demo run should generate both feeds end-to-end using the
    real generator configuration, writing small JSON batches that are
    suitable for a quick, under-a-minute demo pipeline.
    """
    output_dir = tmp_path / "out"

    exit_code = cli_main(
        [
            "--config-path",
            "config/generator.yaml",
            "--sample",
            "--debug-sample",
            "--debug-seed",
            "42",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0

    order_json = output_dir / "order_events" / "json" / "sample.jsonl"
    courier_json = output_dir / "courier_status" / "json" / "sample.jsonl"

    assert order_json.is_file()
    assert courier_json.is_file()

    order_records = _load_jsonl(order_json)
    courier_records = _load_jsonl(courier_json)

    # Both feeds should have at least one record in a debug demo run,
    # but counts should remain small enough for quick inspection.
    assert 1 <= len(order_records) <= 1_000
    assert 1 <= len(courier_records) <= 1_000

    # Debug-mode runs must also respect the entity caps applied by the CLI
    # (for example debug_mode_max_entity_count = 20) at the actual data level.
    restaurant_ids = {rec["restaurant_id"] for rec in order_records}
    courier_ids = {rec["courier_id"] for rec in order_records}

    assert len(restaurant_ids) <= 20
    assert len(courier_ids) <= 20


def test_debug_demo_includes_edge_cases_with_nonzero_rates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    When edge-case rates are non-zero in the generator configuration, a
    debug-style demo run should surface at least some observable edge cases
    even under the capped, low-volume debug settings.
    """
    # Point the project root override at a temporary directory and write a
    # small config that enables multiple edge-case behaviors.
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    cfg_path = tmp_path / "generator.yaml"
    cfg_path.write_text(
        "\n".join(
            [
                "zone_count: 3",
                "restaurant_count: 10",
                "courier_count: 15",
                "demand_level: medium",
                "events_per_second: 200",
                "sample_batch_size_per_feed: 50",
                "debug_mode_max_events_per_second: 100",
                "debug_mode_max_entity_count: 20",
                "late_event_rate: 0.3",
                "duplicate_rate: 0.4",
                "missing_step_rate: 0.2",
                "impossible_duration_rate: 0.4",
                "courier_offline_rate: 0.4",
            ]
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"

    exit_code = cli_main(
        [
            "--config-path",
            "generator.yaml",
            "--sample",
            "--debug-sample",
            "--debug-seed",
            "7",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0

    order_json = output_dir / "order_events" / "json" / "sample.jsonl"
    courier_json = output_dir / "courier_status" / "json" / "sample.jsonl"

    assert order_json.is_file()
    assert courier_json.is_file()

    order_records = _load_jsonl(order_json)
    courier_records = _load_jsonl(courier_json)

    # At least one courier event should be toggled to OFFLINE when
    # courier_offline_rate is non-zero.
    offline_count = sum(1 for rec in courier_records if rec["status"] == "OFFLINE")
    assert offline_count > 0

    # At least one order should exhibit an impossible duration when the
    # corresponding rate is non-zero.
    large_durations = [
        rec["delivery_time_seconds"]
        for rec in order_records
        if rec.get("delivery_time_seconds") is not None
        and rec["delivery_time_seconds"] > 4 * 60 * 60
    ]
    assert large_durations, "expected some inflated delivery_time_seconds for impossible durations"


def test_edge_case_demo_config_produces_observable_edge_cases(tmp_path: Path) -> None:
    """
    The Story 1.6 edge-case demo configuration should produce observable edge cases
    when used in a debug-style sample run.
    """
    output_dir = tmp_path / "edge_case_demo"

    exit_code = cli_main(
        [
            "--config-path",
            "config/generator_edge_cases_demo.yaml",
            "--sample",
            "--debug-sample",
            "--debug-seed",
            "7",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0

    order_json = output_dir / "order_events" / "json" / "sample.jsonl"
    courier_json = output_dir / "courier_status" / "json" / "sample.jsonl"

    assert order_json.is_file()
    assert courier_json.is_file()

    order_records = _load_jsonl(order_json)
    courier_records = _load_jsonl(courier_json)

    assert order_records, "Expected some order_events records from edge-case demo config"
    assert courier_records, "Expected some courier_status records from edge-case demo config"

    offline_count = sum(1 for rec in courier_records if rec["status"] == "OFFLINE")
    assert offline_count > 0

    large_durations = [
        rec["delivery_time_seconds"]
        for rec in order_records
        if rec.get("delivery_time_seconds") is not None
        and rec["delivery_time_seconds"] > 4 * 60 * 60
    ]
    assert large_durations, "expected inflated delivery_time_seconds for impossible durations in edge-case demo config"

