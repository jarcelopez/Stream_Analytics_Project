from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from stream_analytics.common.config import load_typed_config

REQUIRED_COLUMNS = (
    "zone_id",
    "restaurant_id",
    "window_start",
    "window_end",
    "active_orders",
    "avg_delivery_time_seconds",
    "cancellation_rate",
)


@dataclass(frozen=True)
class KpiSnapshot:
    total_active_orders: int
    avg_delivery_time_seconds: float
    cancellation_rate: float


class DashboardConfig(BaseModel):
    metrics_path: str = Field(default="data/metrics_by_zone_restaurant_window", min_length=1)
    refresh_seconds: int = Field(default=15, ge=1)


class MetricsCache:
    def __init__(self, *, ttl_seconds: float, now_fn: Callable[[], float] | None = None) -> None:
        self._ttl_seconds = ttl_seconds
        self._now_fn = now_fn or time.time
        self._cached_value = None
        self._cached_at = 0.0

    def get(self, loader: Callable[[], "pd.DataFrame"]) -> "pd.DataFrame":
        now = self._now_fn()
        if self._cached_value is None or (now - self._cached_at) >= self._ttl_seconds:
            self._cached_value = loader()
            self._cached_at = now
        return self._cached_value.copy()


def load_dashboard_config() -> DashboardConfig:
    return load_typed_config(
        relative_yaml_path="config/dashboard.yaml",
        model_type=DashboardConfig,
        env_prefix="DASHBOARD_",
    )


def load_metrics_dataset(metrics_path: str) -> "pd.DataFrame":
    pd = _import_pandas()
    path = Path(metrics_path)
    if not _looks_like_remote_uri(metrics_path) and not path.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    frame = pd.read_parquet(metrics_path)
    _assert_required_columns(frame.columns)
    return frame


def build_kpi_snapshot(frame: "pd.DataFrame") -> KpiSnapshot:
    if frame.empty:
        return KpiSnapshot(total_active_orders=0, avg_delivery_time_seconds=0.0, cancellation_rate=0.0)
    return KpiSnapshot(
        total_active_orders=int(frame["active_orders"].fillna(0).sum()),
        avg_delivery_time_seconds=float(frame["avg_delivery_time_seconds"].fillna(0).mean()),
        cancellation_rate=float(frame["cancellation_rate"].fillna(0).mean()),
    )


def prepare_time_series(frame: "pd.DataFrame") -> "pd.DataFrame":
    pd = _import_pandas()
    if frame.empty:
        return pd.DataFrame(columns=["window_start", "window_end", "active_orders", "avg_delivery_time_seconds", "cancellation_rate"])

    ordered = frame.sort_values(by=["window_start", "window_end"]).copy()
    return ordered[["window_start", "window_end", "active_orders", "avg_delivery_time_seconds", "cancellation_rate"]]


def apply_overview_filters(frame: "pd.DataFrame") -> "pd.DataFrame":
    # Story 4.2 introduces filter controls; this function keeps the chart pipeline ready.
    return frame


def run() -> None:
    st = _import_streamlit()
    config = load_dashboard_config()
    cache = st.session_state.get("_overview_metrics_cache")
    if not isinstance(cache, MetricsCache) or cache._ttl_seconds != float(config.refresh_seconds):
        cache = MetricsCache(ttl_seconds=float(config.refresh_seconds))
        st.session_state["_overview_metrics_cache"] = cache

    st.set_page_config(page_title="Stream Analytics Overview", layout="wide")
    st.title("Stream Analytics - Overview")
    st.caption("Curated KPI view from metrics parquet outputs.")
    auto_refresh = st.toggle("Auto-refresh", value=True)
    if auto_refresh:
        _schedule_rerun(st=st, refresh_seconds=config.refresh_seconds)

    try:
        with st.spinner("Loading latest metrics..."):
            frame = cache.get(lambda: load_metrics_dataset(config.metrics_path))
    except Exception as exc:  # pragma: no cover - UI path
        st.error(f"Unable to load metrics parquet dataset: {exc}")
        return

    if frame.empty:
        st.info("No metrics data available yet. Once Spark writes curated parquet outputs, KPIs and charts will appear here.")
        return

    filtered = apply_overview_filters(frame)
    snapshot = build_kpi_snapshot(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Active Orders", snapshot.total_active_orders)
    c2.metric("Avg Delivery Time (s)", f"{snapshot.avg_delivery_time_seconds:.2f}")
    c3.metric("Cancellation Rate", f"{snapshot.cancellation_rate * 100:.2f}%")

    time_series = prepare_time_series(filtered)
    st.subheader("Active Orders Trend")
    chart_frame = time_series[["window_start", "active_orders"]].set_index("window_start")
    st.line_chart(chart_frame)
    st.caption(
        f"Cache TTL: {config.refresh_seconds}s. Auto-refresh: {'on' if auto_refresh else 'off'}."
    )


def _assert_required_columns(columns: "pd.Index") -> None:
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise ValueError(f"Missing required dashboard metrics columns: {missing}")


def _looks_like_remote_uri(path: str) -> bool:
    return "://" in path


def _schedule_rerun(*, st, refresh_seconds: int) -> None:
    refresh_seconds = max(refresh_seconds, 1)
    now = time.time()
    next_refresh_at = st.session_state.get("_overview_next_refresh_at")
    if not next_refresh_at:
        st.session_state["_overview_next_refresh_at"] = now + refresh_seconds
        return
    if now >= float(next_refresh_at):
        st.session_state["_overview_next_refresh_at"] = now + refresh_seconds
        st.rerun()


def _import_pandas():
    try:
        import pandas as pd
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError(
            "pandas is required for dashboard metrics loading. Install pandas before running dashboard features."
        ) from exc
    return pd


def _import_streamlit():
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError(
            "streamlit is required to run the dashboard app. Install streamlit before launching the overview page."
        ) from exc
    return st


if __name__ == "__main__":  # pragma: no cover - manual entrypoint
    run()

