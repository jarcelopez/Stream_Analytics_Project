from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_log_record(
    component: str,
    level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "timestamp": _utc_now_iso(),
        "component": component,
        "level": level.upper(),
        "message": message,
    }
    if details is not None:
        record["details"] = details
    return record


def log_info(component: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    record = _base_log_record(component=component, level="INFO", message=message, details=details)
    print(json.dumps(record), file=sys.stdout)


def log_error(component: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    record = _base_log_record(component=component, level="ERROR", message=message, details=details)
    print(json.dumps(record), file=sys.stderr)

