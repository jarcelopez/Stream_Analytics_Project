from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ALLOWED_STATUSES = {"RUNNING", "STOPPED", "ERROR"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_status_payload(payload: dict[str, Any] | None, *, default_status: str = "STOPPED") -> dict[str, Any]:
    raw = dict(payload or {})
    status = str(raw.get("status", default_status)).upper()
    if status not in _ALLOWED_STATUSES:
        status = "ERROR"

    return {
        "status": status,
        "last_heartbeat_ts": str(raw.get("last_heartbeat_ts") or utc_now_iso()),
        "last_batch_ts": raw.get("last_batch_ts"),
        "debug_mode": bool(raw.get("debug_mode", False)),
        "message": str(raw.get("message") or ""),
    }


def write_status_file(
    path: Path,
    *,
    status: str,
    debug_mode: bool,
    last_batch_ts: str | None = None,
    message: str = "",
) -> dict[str, Any]:
    payload = normalize_status_payload(
        {
            "status": status,
            "last_heartbeat_ts": utc_now_iso(),
            "last_batch_ts": last_batch_ts,
            "debug_mode": debug_mode,
            "message": message,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def read_status_file(path: Path, *, default_status: str = "STOPPED") -> dict[str, Any]:
    if not path.exists():
        return normalize_status_payload(
            {"status": default_status, "message": f"Missing status file: {path.name}"},
            default_status=default_status,
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return normalize_status_payload(
            {"status": "ERROR", "message": f"Corrupt status file: {path.name}"},
            default_status=default_status,
        )
    if not isinstance(raw, dict):
        return normalize_status_payload(
            {"status": "ERROR", "message": f"Invalid status format: {path.name}"},
            default_status=default_status,
        )
    return normalize_status_payload(raw, default_status=default_status)
