from __future__ import annotations

from pathlib import Path

from stream_analytics.orchestration.status_files import read_status_file


def test_read_status_file_missing_file_returns_actionable_fallback(tmp_path: Path):
    payload = read_status_file(tmp_path / "spark_job_status.json")
    assert payload["status"] == "STOPPED"
    assert "Missing status file" in payload["message"]
    assert set(payload) == {"status", "last_heartbeat_ts", "last_batch_ts", "debug_mode", "message"}


def test_read_status_file_corrupt_file_returns_error_payload(tmp_path: Path):
    status_path = tmp_path / "generator_status.json"
    status_path.write_text("{bad-json", encoding="utf-8")
    payload = read_status_file(status_path)
    assert payload["status"] == "ERROR"
    assert "Corrupt status file" in payload["message"]
    assert set(payload) == {"status", "last_heartbeat_ts", "last_batch_ts", "debug_mode", "message"}
