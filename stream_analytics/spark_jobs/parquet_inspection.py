from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

METRICS_DATASET_NAME = "metrics_by_zone_restaurant_window"
REQUIRED_METRICS_COLUMNS: Sequence[str] = (
    "zone_id",
    "restaurant_id",
    "window_start",
    "window_end",
    "active_orders",
    "avg_delivery_time_seconds",
    "cancellation_rate",
    "total_orders",
    "active_couriers",
    "orders_per_active_courier",
    "delivery_time_ratio",
    "zone_stress_index",
    "stress_threshold",
    "is_stressed",
)


def assert_required_columns(columns: Iterable[str]) -> None:
    present = set(columns)
    missing = [name for name in REQUIRED_METRICS_COLUMNS if name not in present]
    if missing:
        raise ValueError(f"Missing required metrics columns: {missing}")


def validate_metrics_row(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in ("zone_id", "restaurant_id"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")

    for key in ("window_start", "window_end"):
        if not isinstance(row.get(key), datetime):
            errors.append(f"{key} must be a datetime value")
    if isinstance(row.get("window_start"), datetime) and isinstance(row.get("window_end"), datetime):
        if row["window_end"] <= row["window_start"]:
            errors.append("window_end must be after window_start")

    _validate_non_negative_number(row, "active_orders", errors, integer_only=True)
    _validate_non_negative_number(row, "total_orders", errors, integer_only=True)
    _validate_non_negative_number(row, "active_couriers", errors, integer_only=True)
    _validate_non_negative_number(row, "avg_delivery_time_seconds", errors, nullable=True)
    _validate_non_negative_number(row, "orders_per_active_courier", errors, nullable=True)
    _validate_bounded_number(row, "cancellation_rate", errors)
    _validate_bounded_number(row, "delivery_time_ratio", errors)
    _validate_bounded_number(row, "zone_stress_index", errors)
    _validate_bounded_number(row, "stress_threshold", errors)
    if not isinstance(row.get("is_stressed"), bool):
        errors.append("is_stressed must be a bool")
    return errors


def read_parquet_records(path: str, *, limit: int = 20) -> List[Dict[str, Any]]:
    target = Path(path)
    if not _looks_like_remote_uri(path) and not target.exists():
        raise FileNotFoundError(f"Parquet path not found: {path}")
    try:
        import pandas as pd
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pandas is required for parquet inspection helper. Install pandas to inspect curated outputs."
        ) from exc
    frame = pd.read_parquet(path)
    return frame.head(limit).to_dict(orient="records")


def build_inspection_sql(path: str) -> str:
    return (
        "SELECT zone_id, restaurant_id, window_start, window_end, total_orders, active_orders, "
        "avg_delivery_time_seconds, cancellation_rate, orders_per_active_courier, "
        "zone_stress_index, is_stressed "
        f"FROM parquet.`{path}` ORDER BY window_start DESC, zone_id, restaurant_id;"
    )


def _validate_non_negative_number(
    row: Dict[str, Any],
    key: str,
    errors: List[str],
    *,
    integer_only: bool = False,
    nullable: bool = False,
) -> None:
    value = row.get(key)
    if value is None and nullable:
        return
    number_types = (int,) if integer_only else (int, float)
    if not isinstance(value, number_types):
        errors.append(f"{key} must be a {'non-negative integer' if integer_only else 'non-negative number'}")
        return
    if value < 0:
        errors.append(f"{key} must be >= 0")


def _validate_bounded_number(row: Dict[str, Any], key: str, errors: List[str]) -> None:
    value = row.get(key)
    if not isinstance(value, (int, float)):
        errors.append(f"{key} must be a number in [0, 1]")
        return
    if value < 0 or value > 1:
        errors.append(f"{key} must be in [0, 1]")


def _looks_like_remote_uri(path: str) -> bool:
    return "://" in path
