from __future__ import annotations

import json
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class GeneratorConfig(BaseModel):
    """
    Core configuration for the synthetic generator.

    This model is intentionally focused on core parameters needed for
    Milestone 1, with reserved fields for later stories (edge cases,
    debug mode, and sample batches).
    """

    zone_count: int = Field(default=3, ge=1, le=1_000)
    restaurant_count: int = Field(default=10, ge=1, le=5_000)
    courier_count: int = Field(default=15, ge=1, le=5_000)

    demand_level: Literal["low", "medium", "high"] = "medium"
    events_per_second: float = Field(default=50.0, gt=0.0, le=10_000.0)

    # Reserved / forward-looking fields for later stories
    debug_mode_max_events_per_second: Optional[float] = Field(default=100.0, gt=0.0, le=1_000.0)
    debug_mode_max_entity_count: Optional[int] = Field(default=20, ge=1, le=1_000)
    sample_batch_size_per_feed: Optional[int] = Field(default=500, ge=1, le=100_000)

    # Edge-case configuration for Story 1.3
    late_event_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probability that an event is emitted late or out-of-order.",
    )
    duplicate_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probability that a duplicate event is emitted for a given logical event.",
    )
    missing_step_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probability that a lifecycle step is dropped or collapsed.",
    )
    impossible_duration_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probability that timestamps are manipulated to create impossible durations.",
    )
    courier_offline_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Probability that a courier is marked offline in a way that affects in-flight orders.",
    )

    # Output configuration for Story 1.2 and beyond
    output_base_dir: str = Field(
        default="samples/generator",
        description="Base directory for generator outputs in file/sample modes.",
    )
    output_formats: List[Literal["json", "avro"]] = Field(
        default_factory=lambda: ["json", "avro"],
        description="Which output formats to produce for each feed.",
    )

    # Forward-looking placeholders for Event Hubs integration (Story 3.1)
    event_hubs_order_topic: Optional[str] = Field(
        default=None,
        description="Optional Event Hubs topic/name for order_events feed.",
    )
    event_hubs_courier_topic: Optional[str] = Field(
        default=None,
        description="Optional Event Hubs topic/name for courier_status feed.",
    )

    @field_validator(
        "restaurant_count",
        "courier_count",
        "zone_count",
        "events_per_second",
        "debug_mode_max_events_per_second",
        "debug_mode_max_entity_count",
        "sample_batch_size_per_feed",
        "late_event_rate",
        "duplicate_rate",
        "missing_step_rate",
        "impossible_duration_rate",
        "courier_offline_rate",
        mode="before",
    )
    @classmethod
    def _coerce_numeric(cls, value):
        # Allow environment variables provided as strings to be coerced.
        if isinstance(value, str) and value.strip() != "":
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                # Let Pydantic surface a validation error with the original value.
                return value
        return value

    @field_validator("output_formats")
    @classmethod
    def _validate_output_formats(cls, value):  # type: ignore[override]
        """
        Validate and normalize output_formats, supporting both YAML lists
        and JSON/string overrides from environment variables.
        """
        allowed = {"json", "avro"}

        # Allow environment-style JSON strings, e.g. '["json"]' or '"json"'.
        if isinstance(value, str):
            raw_items: list[str]
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    raw_items = [str(v) for v in parsed]
                else:
                    raw_items = [str(parsed)]
            except Exception:
                # Fallback to simple comma-separated parsing.
                raw_items = [v for v in value.split(",")]
        else:
            raw_items = list(value or [])

        cleaned = [v.strip().lower() for v in raw_items if v and v.strip()]
        if not cleaned:
            raise ValueError("output_formats must contain at least one of: json, avro")
        invalid = [v for v in cleaned if v not in allowed]
        if invalid:
            raise ValueError(f"Unsupported output format(s): {invalid} (allowed: json, avro)")
        # Preserve order but de-duplicate
        seen = set()
        unique: List[str] = []
        for fmt in cleaned:
            if fmt not in seen:
                seen.add(fmt)
                unique.append(fmt)
        return unique

    @model_validator(mode="after")
    def _validate_edge_case_rate_combinations(self) -> "GeneratorConfig":
        """
        Validate that the combined edge-case rates are within a sensible range.

        While multiple edge cases can apply to the same logical event, an
        extremely high combined rate is usually a misconfiguration rather than
        an intentional teaching scenario.
        """
        total_rate = (
            self.late_event_rate
            + self.duplicate_rate
            + self.missing_step_rate
            + self.impossible_duration_rate
            + self.courier_offline_rate
        )
        # Allow overlapping edge cases, but guard against extreme configurations.
        if total_rate > 3.0 + 1e-9:
            raise ValueError(
                "Combined edge-case rates must not exceed 3.0 "
                "(300% of events, allowing overlaps). "
                f"Got total_rate={total_rate!r}."
            )
        return self

