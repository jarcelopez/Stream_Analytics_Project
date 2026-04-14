from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from stream_analytics.spark_jobs.config_models import SparkIngestionConfig


def _window_floor(epoch_seconds: int, size_seconds: int) -> int:
    return (epoch_seconds // size_seconds) * size_seconds


def compute_windowed_kpi_rows(
    order_events: Iterable[Mapping[str, Any]],
    courier_status: Iterable[Mapping[str, Any]],
    *,
    window_duration_seconds: int,
) -> List[Dict[str, Any]]:
    """
    Deterministic helper used by tests to validate KPI math independent of Spark runtime.
    """
    buckets: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
    zone_window_active_couriers: Dict[Tuple[str, int], set[str]] = defaultdict(set)

    for row in courier_status:
        event_time = int(row.get("event_time", 0))
        zone_id = str(row.get("zone_id", "")).strip()
        courier_id = str(row.get("courier_id", "")).strip()
        status = str(row.get("status", "")).upper()
        if not zone_id or not courier_id:
            continue
        if status == "OFFLINE":
            continue
        window_start = _window_floor(event_time // 1_000_000, window_duration_seconds)
        zone_window_active_couriers[(zone_id, window_start)].add(courier_id)

    for row in order_events:
        event_time = int(row.get("event_time", 0))
        zone_id = str(row.get("zone_id", "")).strip()
        restaurant_id = str(row.get("restaurant_id", "")).strip()
        order_id = str(row.get("order_id", "")).strip()
        status = str(row.get("status", "")).upper()
        delivery_time_seconds = row.get("delivery_time_seconds")
        if not zone_id or not restaurant_id or not order_id:
            continue
        window_start = _window_floor(event_time // 1_000_000, window_duration_seconds)
        key = (zone_id, restaurant_id, window_start)
        state = buckets.setdefault(
            key,
            {
                "order_ids": set(),
                "active_order_ids": set(),
                "cancelled_order_ids": set(),
                "delivery_samples": [],
            },
        )
        state["order_ids"].add(order_id)
        if status in {"CREATED", "ACCEPTED", "ASSIGNED", "PICKED_UP"}:
            state["active_order_ids"].add(order_id)
        if status == "CANCELLED":
            state["cancelled_order_ids"].add(order_id)
        if status == "DELIVERED" and isinstance(delivery_time_seconds, (int, float)):
            state["delivery_samples"].append(float(delivery_time_seconds))

    output: List[Dict[str, Any]] = []
    for (zone_id, restaurant_id, window_start), state in sorted(buckets.items()):
        total_orders = len(state["order_ids"])
        active_orders = len(state["active_order_ids"])
        cancellations = len(state["cancelled_order_ids"])
        delivery_samples = state["delivery_samples"]
        avg_delivery_time_seconds = (
            sum(delivery_samples) / len(delivery_samples) if delivery_samples else None
        )
        cancellation_rate = (cancellations / total_orders) if total_orders else 0.0
        active_couriers = len(zone_window_active_couriers.get((zone_id, window_start), set()))
        output.append(
            {
                "zone_id": zone_id,
                "restaurant_id": restaurant_id,
                "window_start": datetime.fromtimestamp(window_start, tz=timezone.utc),
                "window_end": datetime.fromtimestamp(window_start + window_duration_seconds, tz=timezone.utc),
                "active_orders": active_orders,
                "avg_delivery_time_seconds": avg_delivery_time_seconds,
                "cancellation_rate": cancellation_rate,
                "total_orders": total_orders,
                "active_couriers": active_couriers,
                "orders_per_active_courier": float(total_orders) / active_couriers if active_couriers > 0 else None,
            }
        )
    return output


def build_windowed_kpi_df(order_valid_df: Any, courier_valid_df: Any, *, cfg: SparkIngestionConfig) -> Any:
    try:
        from pyspark.sql import functions as F
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pyspark is required for KPI streaming analytics. Install pyspark to run KPI jobs."
        ) from exc

    order_windows = (
        order_valid_df.withWatermark("event_time_ts", cfg.watermark_delay)
        .groupBy(
            F.window(F.col("event_time_ts"), cfg.window_duration, cfg.window_slide).alias("window"),
            F.col("zone_id"),
            F.col("restaurant_id"),
        )
        .agg(
            F.countDistinct("order_id").alias("total_orders"),
            F.countDistinct(
                F.when(
                    F.col("status").isin("CREATED", "ACCEPTED", "ASSIGNED", "PICKED_UP"),
                    F.col("order_id"),
                )
            ).alias("active_orders"),
            F.avg(F.when(F.col("status") == "DELIVERED", F.col("delivery_time_seconds"))).alias(
                "avg_delivery_time_seconds"
            ),
            (
                F.countDistinct(F.when(F.col("status") == "CANCELLED", F.col("order_id")))
                / F.countDistinct("order_id")
            ).alias("cancellation_rate"),
        )
    )

    courier_windows = (
        courier_valid_df.withWatermark("event_time_ts", cfg.watermark_delay)
        .groupBy(
            F.window(F.col("event_time_ts"), cfg.window_duration, cfg.window_slide).alias("window"),
            F.col("zone_id"),
        )
        .agg(
            F.countDistinct(F.when(F.col("status") != "OFFLINE", F.col("courier_id"))).alias("active_couriers"),
        )
    )

    joined = order_windows.join(
        courier_windows,
        on=[
            order_windows["window"] == courier_windows["window"],
            order_windows["zone_id"] == courier_windows["zone_id"],
        ],
        how="left",
    )

    return joined.select(
        order_windows["zone_id"].alias("zone_id"),
        order_windows["restaurant_id"].alias("restaurant_id"),
        order_windows["window.start"].alias("window_start"),
        order_windows["window.end"].alias("window_end"),
        F.col("active_orders"),
        F.col("avg_delivery_time_seconds"),
        F.coalesce(F.col("cancellation_rate"), F.lit(0.0)).alias("cancellation_rate"),
        F.col("total_orders"),
        F.coalesce(F.col("active_couriers"), F.lit(0)).alias("active_couriers"),
        F.when(F.col("active_couriers") > 0, F.col("total_orders") / F.col("active_couriers"))
        .otherwise(F.lit(None))
        .alias("orders_per_active_courier"),
    )
