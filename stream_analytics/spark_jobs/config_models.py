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

    @field_validator("order_event_hub_name", "courier_event_hub_name", "consumer_group", "checkpoint_base_dir", "error_sink_path")
    @classmethod
    def _strip_and_validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must be a non-empty string")
        return normalized

