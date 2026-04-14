from __future__ import annotations

from typing import Any, Dict


def compute_zone_stress_values(
    *,
    cancellation_rate: float,
    avg_delivery_time_seconds: float | None,
    orders_per_active_courier: float | None,
    stress_index_threshold: float,
) -> Dict[str, float | bool]:
    """
    Deterministic helper for unit tests and documentation examples.
    Mirrors the Spark expression logic in add_zone_stress_metrics.
    """
    baseline_delivery_seconds = 1800.0
    safe_delivery_ratio = (
        0.0
        if avg_delivery_time_seconds is None
        else min(avg_delivery_time_seconds / baseline_delivery_seconds, 2.0)
    )
    courier_pressure = (
        1.0
        if orders_per_active_courier is None
        else min(orders_per_active_courier / 4.0, 2.0)
    )
    zone_stress_index = (
        0.4 * float(cancellation_rate)
        + 0.35 * float(safe_delivery_ratio)
        + 0.25 * float(courier_pressure)
    )
    return {
        "delivery_time_ratio": float(safe_delivery_ratio),
        "zone_stress_index": float(zone_stress_index),
        "stress_threshold": float(stress_index_threshold),
        "is_stressed": bool(zone_stress_index >= stress_index_threshold),
    }


def add_zone_stress_metrics(metrics_df: Any, *, stress_index_threshold: float) -> Any:
    """
    Add advanced stress/anomaly metrics expected by dashboard health views.
    """
    try:
        from pyspark.sql import functions as F
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pyspark is required for anomaly score analytics. Install pyspark to run anomaly jobs."
        ) from exc

    baseline_delivery_seconds = F.lit(1800.0)  # 30-minute baseline for demo.
    safe_delivery_ratio = F.when(F.col("avg_delivery_time_seconds").isNull(), F.lit(0.0)).otherwise(
        F.least(F.col("avg_delivery_time_seconds") / baseline_delivery_seconds, F.lit(2.0))
    )
    courier_pressure = F.when(F.col("orders_per_active_courier").isNull(), F.lit(1.0)).otherwise(
        F.least(F.col("orders_per_active_courier") / F.lit(4.0), F.lit(2.0))
    )

    zone_stress_index = (
        F.lit(0.4) * F.col("cancellation_rate")
        + F.lit(0.35) * safe_delivery_ratio
        + F.lit(0.25) * courier_pressure
    )

    return (
        metrics_df.withColumn("delivery_time_ratio", safe_delivery_ratio)
        .withColumn("zone_stress_index", zone_stress_index)
        .withColumn("stress_threshold", F.lit(stress_index_threshold))
        .withColumn("is_stressed", F.col("zone_stress_index") >= F.lit(stress_index_threshold))
    )
