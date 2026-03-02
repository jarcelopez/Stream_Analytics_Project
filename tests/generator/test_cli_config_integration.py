from __future__ import annotations

import json
from pathlib import Path
from typing import List

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
    last_record = json.loads(stderr_lines[-1])
    assert last_record.get("component") == "generator_config"
    assert last_record.get("level") == "ERROR"
    assert "details" in last_record
    errors = last_record["details"].get("errors", [])
    assert any(err.get("field") == "zone_count" for err in errors)

