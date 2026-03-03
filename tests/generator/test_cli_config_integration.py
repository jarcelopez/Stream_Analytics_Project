from __future__ import annotations

import json
from pathlib import Path
from stream_analytics.generator.cli import main as cli_main


def _write_yaml(tmp_path: Path, content: str) -> Path:
    cfg_path = tmp_path / "generator.yaml"
    cfg_path.write_text(content, encoding="utf-8")
    return cfg_path


def test_cli_print_config(tmp_path, capsys, monkeypatch):
    content = """
zone_count: 5
restaurant_count: 8
courier_count: 9
demand_level: low
events_per_second: 25
"""
    cfg_path = _write_yaml(tmp_path, content)
    # Point the project root override at our temp directory so the loader finds this file.
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    exit_code = cli_main(["--config-path", "generator.yaml", "--print-config"])
    captured = capsys.readouterr()
    assert exit_code == 0

    # The CLI prints a JSON object with a `config` field.
    payload = json.loads(captured.out.strip().splitlines()[-1])
    cfg = payload["config"]
    assert cfg["zone_count"] == 5
    assert cfg["restaurant_count"] == 8
    assert cfg["courier_count"] == 9
    assert cfg["demand_level"] == "low"
    assert cfg["events_per_second"] == 25


def test_cli_invalid_config_emits_error_and_nonzero_exit(tmp_path, capsys, monkeypatch):
    content = """
zone_count: -1
restaurant_count: 10
courier_count: 5
"""
    cfg_path = _write_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    exit_code = cli_main(["--config-path", "generator.yaml"])
    captured = capsys.readouterr()

    assert exit_code == 1
    # At least one structured error record should be printed to stderr.
    stderr_lines = [line for line in captured.err.splitlines() if line.strip()]
    assert stderr_lines, "expected structured error output on stderr"
    records = [json.loads(line) for line in stderr_lines]

    # Ensure that the shared config loader logged a validation error record.
    config_records = [rec for rec in records if rec.get("component") == "generator_config"]
    assert config_records, "expected at least one generator_config validation error record"

    # The validation record should include per-field error details for zone_count.
    details_errors = []
    for rec in config_records:
        details = rec.get("details") or {}
        details_errors.extend(details.get("errors", []))
    assert any(err.get("field") == "zone_count" for err in details_errors)


def test_debug_sample_clamps_entities_and_events_per_second(tmp_path, monkeypatch):
    """
    Debug-style sample runs should respect the debug-mode caps for both
    entity counts and effective events_per_second, ensuring low-volume
    demo settings even if the base config requests higher throughput.
    """
    content = """
zone_count: 10
restaurant_count: 50
courier_count: 60
demand_level: medium
events_per_second: 500
debug_mode_max_events_per_second: 100
debug_mode_max_entity_count: 20
sample_batch_size_per_feed: 5
"""
    _write_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    captured_configs: list[dict] = []

    def _fake_generate_sample_feeds(*, config, base_output_dir):
        # Capture the effective config as a plain dict for assertions.
        captured_configs.append(config.model_dump())

    monkeypatch.setattr(
        "stream_analytics.generator.cli.generate_sample_feeds",
        _fake_generate_sample_feeds,
    )

    exit_code = cli_main(
        [
            "--config-path",
            "generator.yaml",
            "--sample",
            "--debug-sample",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert exit_code == 0
    assert captured_configs, "expected generate_sample_feeds to be called in debug mode"

    effective = captured_configs[0]

    # Entity-related knobs should be clamped to the debug maximum.
    assert effective["zone_count"] <= 20
    assert effective["restaurant_count"] <= 20
    assert effective["courier_count"] <= 20

    # Throughput configuration should also respect the debug-mode ceiling.
    assert effective["events_per_second"] <= 100


def test_debug_sample_seeds_randomness_for_reproducibility(tmp_path, monkeypatch):
    """
    Debug sample runs must seed the generator so that repeating the command
    with the same configuration and debug seed is reproducible.
    """
    content = """
zone_count: 5
restaurant_count: 5
courier_count: 5
demand_level: low
events_per_second: 50
sample_batch_size_per_feed: 5
"""
    _write_yaml(tmp_path, content)
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))

    calls: list[int] = []

    def _fake_seed_for_debug(seed: int) -> None:
        calls.append(seed)

    def _fake_generate_sample_feeds(*, config, base_output_dir):
        # No-op; we only care that seeding is invoked as expected.
        return None

    monkeypatch.setattr(
        "stream_analytics.generator.cli.seed_for_debug",
        _fake_seed_for_debug,
    )
    monkeypatch.setattr(
        "stream_analytics.generator.cli.generate_sample_feeds",
        _fake_generate_sample_feeds,
    )

    exit_code = cli_main(
        [
            "--config-path",
            "generator.yaml",
            "--sample",
            "--debug-sample",
            "--debug-seed",
            "123",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert exit_code == 0
    assert calls == [123]

