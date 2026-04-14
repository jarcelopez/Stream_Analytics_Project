from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from stream_analytics.common.logging_utils import log_info
from stream_analytics.spark_jobs.config_models import SparkIngestionConfig, _parse_duration_seconds

_COMPONENT = "spark_windowing"


def build_windowed_count_df(valid_df: Any, *, cfg: SparkIngestionConfig, feed_name: str) -> Any:
    """
    Build a windowed count dataframe with explicit watermark semantics.
    """
    try:
        from pyspark.sql import functions as F
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pyspark is required for windowed streaming analytics. Install pyspark to run Spark windowing jobs."
        ) from exc

    return (
        valid_df.withWatermark("event_time_ts", cfg.watermark_delay)
        .groupBy(F.window(F.col("event_time_ts"), cfg.window_duration, cfg.window_slide), F.col("zone_id"))
        .count()
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            F.col("zone_id"),
            F.lit(feed_name).alias("feed_type"),
            F.col("count").alias("event_count"),
        )
    )


def log_windowing_startup(*, cfg: SparkIngestionConfig, checkpoint_path: str, output_mode: str) -> None:
    log_info(
        _COMPONENT,
        "windowing configuration initialized",
        {
            "watermark_delay": cfg.watermark_delay,
            "window_duration": cfg.window_duration,
            "window_slide": cfg.window_slide,
            "window_output_mode": output_mode,
            "window_checkpoint_path": checkpoint_path,
            "timezone_assumption": "UTC",
        },
    )


def summarize_late_event_handling(
    event_time_micros: Iterable[int], *, watermark_delay: str, window_duration: str
) -> Dict[str, int]:
    """
    Deterministic helper to reason about watermark behavior in tests.
    """
    watermark_delay_micros = _parse_duration_seconds(watermark_delay) * 1_000_000
    window_duration_micros = _parse_duration_seconds(window_duration) * 1_000_000

    times: List[int] = list(event_time_micros)
    if not times:
        return {
            "accepted_records": 0,
            "accepted_late_records": 0,
            "too_late_dropped_records": 0,
            "watermark_micros": 0,
            "max_event_time_micros": 0,
        }

    max_event_time = max(times)
    watermark = max_event_time - watermark_delay_micros
    accepted_records = 0
    accepted_late_records = 0
    too_late_dropped_records = 0

    for value in times:
        # Too-late boundary mirrors event-time stateful behavior:
        # rows older than watermark are dropped from stateful aggregations.
        if value < watermark:
            too_late_dropped_records += 1
            continue
        accepted_records += 1
        if value < max_event_time:
            accepted_late_records += 1

    return {
        "accepted_records": accepted_records,
        "accepted_late_records": accepted_late_records,
        "too_late_dropped_records": too_late_dropped_records,
        "watermark_micros": watermark,
        "max_event_time_micros": max_event_time,
        "window_duration_micros": window_duration_micros,
    }


def log_batch_watermark_observability(
    *,
    feed_name: str,
    batch_id: int,
    summary: Mapping[str, int],
    trigger_ts: str,
    dropped_by_watermark_rows: int | None = None,
) -> None:
    details: Dict[str, int | str | None] = {
        "feed_type": feed_name,
        "batch_id": batch_id,
        "trigger_ts": trigger_ts,
        "current_batch_watermark_micros_estimate": summary.get("watermark_micros", 0),
        "accepted_records_estimate": summary.get("accepted_records", 0),
        "accepted_late_records_estimate": summary.get("accepted_late_records", 0),
        "too_late_dropped_records_estimate": summary.get("too_late_dropped_records", 0),
        "dropped_by_watermark_rows": dropped_by_watermark_rows,
    }
    log_info(
        _COMPONENT,
        "window batch observability",
        details,
    )
