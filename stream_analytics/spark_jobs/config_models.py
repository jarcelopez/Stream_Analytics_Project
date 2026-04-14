from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SparkIngestionConfig(BaseModel):
    order_event_hub_name: str = Field(min_length=1)
    courier_event_hub_name: str = Field(min_length=1)

    consumer_group: str = Field(default="$Default", min_length=1)
    starting_position: Literal["latest", "earliest"] = "latest"

    checkpoint_base_dir: str = Field(default="checkpoints/spark_jobs", min_length=1)
    error_sink_path: str = Field(default="logs/spark_ingestion_errors.jsonl", min_length=1)
    metrics_sink_path: str = Field(default="data/metrics_by_zone_restaurant_window", min_length=1)
    metrics_checkpoint_dir: str = Field(default="checkpoints/spark_jobs/metrics_by_zone_restaurant_window", min_length=1)
    watermark_delay: str = Field(default="10 minutes", min_length=1)
    window_duration: str = Field(default="10 minutes", min_length=1)
    window_slide: str = Field(default="5 minutes", min_length=1)
    # Parquet file sinks for metrics are append-only in this project setup.
    window_output_mode: Literal["append"] = "append"
    stress_index_threshold: float = Field(default=0.75, ge=0.0)

    @field_validator(
        "order_event_hub_name",
        "courier_event_hub_name",
        "consumer_group",
        "checkpoint_base_dir",
        "error_sink_path",
        "metrics_sink_path",
        "metrics_checkpoint_dir",
        "watermark_delay",
        "window_duration",
        "window_slide",
    )
    @classmethod
    def _strip_and_validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must be a non-empty string")
        return normalized

    @field_validator("watermark_delay", "window_duration", "window_slide")
    @classmethod
    def _validate_duration_string(cls, value: str) -> str:
        _parse_duration_seconds(value)
        return value

    @field_validator("watermark_delay")
    @classmethod
    def _validate_positive_watermark(cls, value: str) -> str:
        if _parse_duration_seconds(value) <= 0:
            raise ValueError("watermark_delay must be greater than zero")
        return value

    @field_validator("window_duration")
    @classmethod
    def _validate_positive_window_duration(cls, value: str) -> str:
        if _parse_duration_seconds(value) <= 0:
            raise ValueError("window_duration must be greater than zero")
        return value

    @field_validator("window_slide")
    @classmethod
    def _validate_slide_against_duration(cls, value: str, info) -> str:
        slide_seconds = _parse_duration_seconds(value)
        if slide_seconds <= 0:
            raise ValueError("window_slide must be greater than zero")

        window_duration = info.data.get("window_duration")
        if isinstance(window_duration, str):
            duration_seconds = _parse_duration_seconds(window_duration)
            if slide_seconds > duration_seconds:
                raise ValueError("window_slide cannot be greater than window_duration")
        return value


def _parse_duration_seconds(duration: str) -> int:
    normalized = " ".join(duration.strip().lower().split())
    parts = normalized.split(" ")
    if len(parts) != 2:
        raise ValueError("duration must use '<integer> <unit>' format, e.g. '10 minutes'")
    amount_raw, unit = parts
    if not amount_raw.isdigit():
        raise ValueError("duration amount must be a positive integer")
    amount = int(amount_raw)
    units = {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
        "day": 86400,
        "days": 86400,
    }
    factor = units.get(unit)
    if factor is None:
        raise ValueError("duration unit must be one of: second(s), minute(s), hour(s), day(s)")
    return amount * factor

