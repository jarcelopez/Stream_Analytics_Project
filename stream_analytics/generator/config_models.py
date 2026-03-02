from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator(
        "restaurant_count",
        "courier_count",
        "zone_count",
        "events_per_second",
        "debug_mode_max_events_per_second",
        "debug_mode_max_entity_count",
        "sample_batch_size_per_feed",
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

