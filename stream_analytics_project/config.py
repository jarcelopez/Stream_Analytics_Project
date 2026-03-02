from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


OutputFormat = Literal["json", "avro", "both"]


@dataclass
class PromoPeriod:
    name: str
    start_hour: int  # 0-23, simulation-local time
    end_hour: int    # 0-23, simulation-local time
    demand_multiplier: float = 1.5


@dataclass
class GeneratorConfig:
    # Global simulation config
    simulation_duration_minutes: int = 60
    events_per_minute_base: int = 200
    time_granularity_seconds: int = 1

    # Entities
    num_zones: int = 8
    num_restaurants: int = 200
    num_couriers: int = 150
    num_customers: int = 5000

    # Temporal patterns
    lunch_peak_hour: int = 13
    dinner_peak_hour: int = 20
    weekday_multiplier: float = 1.0
    weekend_multiplier: float = 1.3
    zone_demand_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "zone_1": 1.4,
            "zone_2": 1.2,
            "zone_3": 1.0,
            "zone_4": 0.8,
        }
    )

    # Economics
    avg_order_value: float = 25.0
    order_value_stddev: float = 10.0
    commission_rate: float = 0.25

    # Operational behaviour
    base_prep_time_minutes: float = 15.0
    base_travel_time_minutes: float = 20.0
    courier_offline_probability_per_hour: float = 0.02
    cancellation_probability: float = 0.03
    promo_periods: List[PromoPeriod] = field(default_factory=list)

    # Edge-case injection
    late_event_fraction: float = 0.05
    duplicate_event_fraction: float = 0.01
    missing_step_fraction: float = 0.01
    impossible_duration_fraction: float = 0.01

    # Output
    output_format: OutputFormat = "both"
    output_path: str = "samples"
    events_per_file: int = 10_000

    # Randomness
    random_seed: Optional[int] = 42


def default_config() -> GeneratorConfig:
    """Return a GeneratorConfig with sensible defaults for local development."""
    return GeneratorConfig()


