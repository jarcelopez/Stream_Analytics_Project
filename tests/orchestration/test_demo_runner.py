from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream_analytics.orchestration.demo_runner import DemoRunnerConfig, derive_run_state, read_demo_status, start_demo, stop_demo


def _config(tmp_path: Path) -> DemoRunnerConfig:
    return DemoRunnerConfig(
        generator_command=["python", "-m", "generator"],
        spark_command=["python", "-m", "spark"],
        status_dir=tmp_path / "status",
    )


def test_derive_run_state_handles_running_and_error_states():
    assert derive_run_state("RUNNING", "RUNNING") == "RUNNING"
    assert derive_run_state("RUNNING", "STOPPED") == "ERROR"
    assert derive_run_state("ERROR", "RUNNING") == "ERROR"


def test_read_demo_status_returns_default_stopped_payloads(tmp_path: Path):
    status = read_demo_status(_config(tmp_path))
    assert status["overall"] == "STOPPED"
    assert status["generator"]["status"] == "STOPPED"
    assert status["spark"]["status"] == "STOPPED"


def test_start_demo_is_idempotent_when_already_running(monkeypatch, tmp_path: Path):
    cfg = _config(tmp_path)
    cfg.status_dir.mkdir(parents=True, exist_ok=True)
    (cfg.status_dir / cfg.generator_status_file).write_text(
        json.dumps({"status": "RUNNING", "debug_mode": False}),
        encoding="utf-8",
    )
    (cfg.status_dir / cfg.spark_status_file).write_text(
        json.dumps({"status": "RUNNING", "debug_mode": False}),
        encoding="utf-8",
    )

    def _fail_spawn(_command):
        raise AssertionError("should not spawn when already running")

    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._spawn_process", _fail_spawn)

    run_state, message = start_demo(cfg)
    assert run_state == "RUNNING"
    assert "idempotent" in message


def test_start_demo_writes_running_status_and_pid_files(monkeypatch, tmp_path: Path):
    cfg = _config(tmp_path)

    class _FakeProcess:
        def __init__(self, pid: int):
            self.pid = pid

    pids = [111, 222]

    def _fake_spawn(_command):
        return _FakeProcess(pids.pop(0))

    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._spawn_process", _fake_spawn)

    run_state, message = start_demo(cfg)
    assert run_state == "RUNNING"
    assert "successfully" in message
    assert (cfg.status_dir / cfg.generator_pid_file).read_text(encoding="utf-8").strip() == "111"
    assert (cfg.status_dir / cfg.spark_pid_file).read_text(encoding="utf-8").strip() == "222"
    assert read_demo_status(cfg)["overall"] == "RUNNING"


def test_stop_demo_is_idempotent_if_no_pid_files(tmp_path: Path):
    cfg = _config(tmp_path)
    run_state, message = stop_demo(cfg, reset=False)
    assert run_state == "STOPPED"
    assert "idempotent" in message


def test_stop_demo_terminates_running_processes_and_resets_state(monkeypatch, tmp_path: Path):
    cfg = _config(tmp_path)
    cfg.status_dir.mkdir(parents=True, exist_ok=True)
    (cfg.status_dir / cfg.generator_pid_file).write_text("111", encoding="utf-8")
    (cfg.status_dir / cfg.spark_pid_file).write_text("222", encoding="utf-8")

    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._is_pid_running", lambda _pid: True)
    killed: list[int] = []
    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._terminate_process_tree", lambda pid: killed.append(pid))

    run_state, _message = stop_demo(cfg, reset=True)
    assert run_state == "STOPPED"
    assert sorted(killed) == [111, 222]
    assert not (cfg.status_dir / cfg.generator_pid_file).exists()
    assert not (cfg.status_dir / cfg.spark_pid_file).exists()


def test_start_demo_cleans_up_generator_if_spark_spawn_fails(monkeypatch, tmp_path: Path):
    cfg = _config(tmp_path)

    class _FakeProcess:
        def __init__(self, pid: int):
            self.pid = pid

    def _fake_spawn(command):
        if command == cfg.generator_command:
            return _FakeProcess(777)
        raise RuntimeError("spark failed")

    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._spawn_process", _fake_spawn)
    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._is_pid_running", lambda _pid: True)
    killed: list[int] = []
    monkeypatch.setattr("stream_analytics.orchestration.demo_runner._terminate_process_tree", lambda pid: killed.append(pid))

    run_state, message = start_demo(cfg)
    assert run_state == "ERROR"
    assert "Failed to start demo processes" in message
    assert killed == [777]
    assert not (cfg.status_dir / cfg.generator_pid_file).exists()
