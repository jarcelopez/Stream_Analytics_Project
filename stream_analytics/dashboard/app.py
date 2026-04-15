from __future__ import annotations

import time
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    time_window_presets: list[str] = Field(default_factory=lambda: ["15m", "1h", "24h"])
    default_time_window: str = Field(default="1h", min_length=1)


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


def apply_overview_filters(
    frame: "pd.DataFrame",
    selected_zone: str,
    selected_restaurant: str,
    selected_window: str,
    *,
    now_utc: datetime | None = None,
) -> "pd.DataFrame":
    pd = _import_pandas()
    filtered = frame.copy()
    if selected_zone != "All zones":
        zone_values = filtered["zone_id"].astype("string")
        filtered = filtered[zone_values == selected_zone]
    if selected_restaurant != "All restaurants":
        restaurant_values = filtered["restaurant_id"].astype("string")
        filtered = filtered[restaurant_values == selected_restaurant]

    delta = _parse_window_preset_to_timedelta(selected_window)
    reference_time = now_utc or datetime.now(UTC)
    threshold = reference_time - delta
    window_end = pd.to_datetime(filtered["window_end"], utc=True, errors="coerce")
    in_window = (window_end >= threshold) & (window_end <= reference_time)
    filtered = filtered[in_window]
    return filtered.sort_values(by=["window_start", "window_end"]).copy()


def format_active_filters(selected_zone: str, selected_restaurant: str, selected_window: str) -> str:
    return (
        "Active filters - "
        f"Zone: {selected_zone}, "
        f"Restaurant: {selected_restaurant}, "
        f"Time window: {selected_window}"
    )


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

    presets = _normalize_window_presets(config.time_window_presets, config.default_time_window)
    default_window = config.default_time_window if config.default_time_window in presets else presets[0]
    zone_options = ["All zones", *sorted(str(value) for value in frame["zone_id"].dropna().unique())]
    restaurant_options = ["All restaurants", *sorted(str(value) for value in frame["restaurant_id"].dropna().unique())]

    controls = st.columns(3)
    selected_zone = controls[0].selectbox("Zone", zone_options, index=0, key="overview_zone_filter")
    selected_restaurant = controls[1].selectbox(
        "Restaurant",
        restaurant_options,
        index=0,
        key="overview_restaurant_filter",
    )
    selected_window = controls[2].selectbox(
        "Time window",
        presets,
        index=presets.index(default_window),
        key="overview_time_window_filter",
    )

    filtered = apply_overview_filters(frame, selected_zone, selected_restaurant, selected_window)
    st.caption(format_active_filters(selected_zone, selected_restaurant, selected_window))
    if filtered.empty:
        st.info("No matching data for the current zone, restaurant, and time-window filters.")
        return

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


def _normalize_window_presets(window_presets: list[str], default_preset: str) -> list[str]:
    presets: list[str] = []
    invalid_presets: list[str] = []
    for preset in window_presets:
        normalized = preset.strip()
        if not normalized:
            continue
        if not _is_valid_window_preset(normalized):
            invalid_presets.append(normalized)
            continue
        if normalized not in presets:
            presets.append(normalized)
    if not presets:
        presets = ["15m", "1h", "24h"]
    if default_preset and not _is_valid_window_preset(default_preset):
        invalid_presets.append(default_preset)
    if default_preset and _is_valid_window_preset(default_preset) and default_preset not in presets:
        presets.insert(0, default_preset)
    if invalid_presets:
        joined = ", ".join(sorted(set(invalid_presets)))
        warnings.warn(
            f"Ignoring invalid dashboard time-window preset(s): {joined}",
            UserWarning,
            stacklevel=2,
        )
    return presets


def _parse_window_preset_to_timedelta(window_preset: str) -> timedelta:
    normalized = window_preset.strip().lower()
    if len(normalized) < 2:
        raise ValueError(f"Invalid time-window preset: {window_preset!r}")
    suffix = normalized[-1]
    amount_str = normalized[:-1]
    if not amount_str.isdigit():
        raise ValueError(f"Invalid time-window preset: {window_preset!r}")
    amount = int(amount_str)
    if amount <= 0:
        raise ValueError(f"Invalid time-window preset: {window_preset!r}")
    if suffix == "m":
        return timedelta(minutes=amount)
    if suffix == "h":
        return timedelta(hours=amount)
    if suffix == "d":
        return timedelta(days=amount)
    raise ValueError(f"Invalid time-window preset: {window_preset!r}")


def _is_valid_window_preset(window_preset: str) -> bool:
    try:
        _parse_window_preset_to_timedelta(window_preset)
    except ValueError:
        return False
    return True


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

