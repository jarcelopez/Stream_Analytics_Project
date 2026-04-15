from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stream_analytics.orchestration.status_files import read_status_file, utc_now_iso, write_status_file

_HEARTBEAT_APPROX_MARKER = "[source:heartbeat-approx]"


def _project_root() -> Path:
    """Repository root (parent of `stream_analytics/`)."""
    return Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class DemoRunnerConfig:
    generator_command: list[str]
    spark_command: list[str]
    status_dir: Path
    generator_status_file: str = "generator_status.json"
    spark_status_file: str = "spark_job_status.json"
    generator_pid_file: str = "generator.pid"
    spark_pid_file: str = "spark.pid"
    debug_mode: bool = False


def read_demo_status(config: DemoRunnerConfig) -> dict[str, Any]:
    _reconcile_demo_processes(config)
    _refresh_runtime_status(config)
    generator = read_status_file(config.status_dir / config.generator_status_file)
    spark = read_status_file(config.status_dir / config.spark_status_file)
    overall = derive_run_state(generator["status"], spark["status"])
    return {"overall": overall, "generator": generator, "spark": spark}


def derive_run_state(generator_status: str, spark_status: str) -> str:
    statuses = {str(generator_status).upper(), str(spark_status).upper()}
    if "ERROR" in statuses:
        return "ERROR"
    if statuses == {"RUNNING"}:
        return "RUNNING"
    if "RUNNING" in statuses and "STOPPED" in statuses:
        return "ERROR"
    return "STOPPED"


def start_demo(config: DemoRunnerConfig) -> tuple[str, str]:
    _validate_start_config(config)
    current = read_demo_status(config)
    if current["overall"] == "RUNNING":
        return "RUNNING", "Demo is already running. Start operation is idempotent."

    generator_proc: subprocess.Popen[Any] | None = None
    try:
        generator_proc = _spawn_process(config.generator_command)
        _write_pid(config.status_dir / config.generator_pid_file, generator_proc.pid)
        spark_proc = _spawn_process(config.spark_command)
        _write_pid(config.status_dir / config.spark_pid_file, spark_proc.pid)
    except Exception as exc:
        if generator_proc is not None and _is_pid_running(generator_proc.pid):
            _terminate_process_tree(generator_proc.pid)
        _remove_file_if_exists(config.status_dir / config.generator_pid_file)
        _remove_file_if_exists(config.status_dir / config.spark_pid_file)
        write_status_file(
            config.status_dir / config.generator_status_file,
            status="ERROR",
            debug_mode=config.debug_mode,
            message=f"Failed to start demo processes: {exc}",
        )
        write_status_file(
            config.status_dir / config.spark_status_file,
            status="ERROR",
            debug_mode=config.debug_mode,
            message=f"Failed to start demo processes: {exc}",
        )
        return "ERROR", f"Failed to start demo processes: {exc}"

    write_status_file(
        config.status_dir / config.generator_status_file,
        status="RUNNING",
        debug_mode=config.debug_mode,
        message="Generator process started from dashboard.",
    )
    write_status_file(
        config.status_dir / config.spark_status_file,
        status="RUNNING",
        debug_mode=config.debug_mode,
        message="Spark process started from dashboard.",
    )
    return "RUNNING", "Demo started successfully."


def stop_demo(config: DemoRunnerConfig, *, reset: bool = False) -> tuple[str, str]:
    killed_any = False
    for pid_file in (config.generator_pid_file, config.spark_pid_file):
        pid_path = config.status_dir / pid_file
        pid = _read_pid(pid_path)
        if pid is not None and _is_pid_running(pid):
            _terminate_process_tree(pid)
            killed_any = True
        _remove_file_if_exists(pid_path)

    message = "Demo reset complete." if reset else "Demo stopped successfully."
    if not killed_any:
        message = "Demo already stopped. Stop operation is idempotent."

    last_batch_ts = None if reset else utc_now_iso()
    write_status_file(
        config.status_dir / config.generator_status_file,
        status="STOPPED",
        debug_mode=config.debug_mode,
        last_batch_ts=last_batch_ts,
        message=message,
    )
    write_status_file(
        config.status_dir / config.spark_status_file,
        status="STOPPED",
        debug_mode=config.debug_mode,
        last_batch_ts=last_batch_ts,
        message=message,
    )
    return "STOPPED", message


def _refresh_runtime_status(config: DemoRunnerConfig) -> None:
    now_ts = utc_now_iso()
    generator_path = config.status_dir / config.generator_status_file
    spark_path = config.status_dir / config.spark_status_file

    generator = read_status_file(generator_path)
    spark = read_status_file(spark_path)

    if str(generator.get("status", "")).upper() == "RUNNING":
        write_status_file(
            generator_path,
            status="RUNNING",
            debug_mode=bool(generator.get("debug_mode", config.debug_mode)),
            last_batch_ts=generator.get("last_batch_ts"),
            message=str(generator.get("message") or "Generator process is running."),
        )

    if str(spark.get("status", "")).upper() != "RUNNING":
        return

    existing_batch_ts = spark.get("last_batch_ts")
    spark_message = str(spark.get("message") or "Spark process is running.")
    approximation_active = _HEARTBEAT_APPROX_MARKER in spark_message
    if not existing_batch_ts or approximation_active:
        existing_batch_ts = now_ts
        if not approximation_active:
            approximation_note = (
                "Last batch timestamp approximated from dashboard heartbeat "
                "(checkpoint timestamp unavailable)."
            )
            spark_message = f"{spark_message} {approximation_note} {_HEARTBEAT_APPROX_MARKER}".strip()

    write_status_file(
        spark_path,
        status="RUNNING",
        debug_mode=bool(spark.get("debug_mode", config.debug_mode)),
        last_batch_ts=existing_batch_ts,
        message=spark_message,
    )


def _validate_start_config(config: DemoRunnerConfig) -> None:
    if not config.generator_command:
        raise ValueError("Missing generator command in dashboard configuration.")
    if not config.spark_command:
        raise ValueError("Missing spark command in dashboard configuration.")


def _reconcile_demo_processes(config: DemoRunnerConfig) -> None:
    """
    If status files claim RUNNING but the recorded PID has exited, mark ERROR.

    The dashboard discards child stderr; a fast-failing Spark job otherwise looks healthy.
    """
    for pid_file, status_file, label in (
        (config.generator_pid_file, config.generator_status_file, "Generator"),
        (config.spark_pid_file, config.spark_status_file, "Spark streaming"),
    ):
        status_path = config.status_dir / status_file
        payload = read_status_file(status_path)
        if str(payload.get("status", "")).upper() != "RUNNING":
            continue
        pid = _read_pid(config.status_dir / pid_file)
        if pid is None:
            continue
        if _is_pid_running(pid):
            continue
        write_status_file(
            status_path,
            status="ERROR",
            debug_mode=bool(payload.get("debug_mode", config.debug_mode)),
            last_batch_ts=payload.get("last_batch_ts"),
            message=(
                f"{label} process (pid {pid}) is no longer running. "
                "Run the same command in a terminal (without redirecting stderr) to see errors."
            ),
        )


def _spawn_process(command: list[str]) -> subprocess.Popen[Any]:
    kwargs: dict[str, Any] = {
        "cwd": str(_project_root()),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["preexec_fn"] = os.setsid
    return subprocess.Popen(command, **kwargs)


def _terminate_process_tree(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    os.killpg(pid, signal.SIGTERM)


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _write_pid(path: Path, pid: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(pid), encoding="utf-8")


def _read_pid(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (TypeError, ValueError, OSError):
        return None


def _remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
