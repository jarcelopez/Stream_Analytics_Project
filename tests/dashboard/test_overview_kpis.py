from __future__ import annotations

from datetime import UTC, datetime
import time

import pandas as pd
import pytest

from stream_analytics.dashboard.app import (
    DashboardConfig,
    MetricsCache,
    apply_overview_filters,
    build_kpi_snapshot,
    format_active_filters,
    run,
    prepare_time_series,
    _normalize_window_presets,
)


def test_build_kpi_snapshot_computes_required_core_values():
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "active_orders": 4,
                "avg_delivery_time_seconds": 600.0,
                "cancellation_rate": 0.25,
            },
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 10, 5, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 15, tzinfo=UTC),
                "active_orders": 2,
                "avg_delivery_time_seconds": 900.0,
                "cancellation_rate": 0.50,
            },
        ]
    )

    result = build_kpi_snapshot(frame)
    assert result.total_active_orders == 6
    assert result.avg_delivery_time_seconds == 750.0
    assert result.cancellation_rate == 0.375


def test_prepare_time_series_returns_time_ordered_columns_for_chart():
    frame = pd.DataFrame(
        [
            {
                "window_start": datetime(2026, 4, 1, 10, 5, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 15, tzinfo=UTC),
                "active_orders": 1,
                "avg_delivery_time_seconds": 700.0,
                "cancellation_rate": 0.1,
            },
            {
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "active_orders": 3,
                "avg_delivery_time_seconds": 850.0,
                "cancellation_rate": 0.3,
            },
        ]
    )

    prepared = prepare_time_series(frame)
    assert list(prepared.columns) == [
        "window_start",
        "window_end",
        "active_orders",
        "avg_delivery_time_seconds",
        "cancellation_rate",
    ]
    assert list(prepared["window_start"]) == [
        datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        datetime(2026, 4, 1, 10, 5, tzinfo=UTC),
    ]


def test_apply_overview_filters_supports_zone_restaurant_and_window():
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 9, 45, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 9, 59, tzinfo=UTC),
                "active_orders": 5,
                "avg_delivery_time_seconds": 500.0,
                "cancellation_rate": 0.1,
            },
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-2",
                "window_start": datetime(2026, 4, 1, 9, 55, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "active_orders": 3,
                "avg_delivery_time_seconds": 700.0,
                "cancellation_rate": 0.2,
            },
            {
                "zone_id": "zone-2",
                "restaurant_id": "rest-3",
                "window_start": datetime(2026, 4, 1, 9, 58, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 12, tzinfo=UTC),
                "active_orders": 8,
                "avg_delivery_time_seconds": 650.0,
                "cancellation_rate": 0.05,
            },
        ]
    )
    now = datetime(2026, 4, 1, 10, 15, tzinfo=UTC)

    zone_only = apply_overview_filters(frame, "zone-1", "All restaurants", "1h", now_utc=now)
    assert set(zone_only["restaurant_id"]) == {"rest-1", "rest-2"}

    restaurant_only = apply_overview_filters(frame, "All zones", "rest-3", "1h", now_utc=now)
    assert set(restaurant_only["zone_id"]) == {"zone-2"}

    combined = apply_overview_filters(frame, "zone-1", "rest-2", "1h", now_utc=now)
    assert len(combined) == 1
    assert combined.iloc[0]["restaurant_id"] == "rest-2"

    no_filter = apply_overview_filters(frame, "All zones", "All restaurants", "1h", now_utc=now)
    assert len(no_filter) == 3

    last_15m = apply_overview_filters(frame, "All zones", "All restaurants", "15m", now_utc=now)
    assert len(last_15m) == 2


def test_apply_overview_filters_matches_numeric_ids_from_string_selection():
    frame = pd.DataFrame(
        [
            {
                "zone_id": 7,
                "restaurant_id": 101,
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "active_orders": 6,
                "avg_delivery_time_seconds": 580.0,
                "cancellation_rate": 0.03,
            }
        ]
    )

    filtered = apply_overview_filters(frame, "7", "101", "1h", now_utc=datetime(2026, 4, 1, 10, 15, tzinfo=UTC))
    assert len(filtered) == 1
    assert filtered.iloc[0]["zone_id"] == 7
    assert filtered.iloc[0]["restaurant_id"] == 101


def test_apply_overview_filters_excludes_future_window_end_rows():
    now = datetime(2026, 4, 1, 10, 0, tzinfo=UTC)
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 9, 45, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 9, 55, tzinfo=UTC),
                "active_orders": 2,
                "avg_delivery_time_seconds": 620.0,
                "cancellation_rate": 0.07,
            },
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 10, 1, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 5, tzinfo=UTC),
                "active_orders": 9,
                "avg_delivery_time_seconds": 480.0,
                "cancellation_rate": 0.02,
            },
        ]
    )

    filtered = apply_overview_filters(frame, "All zones", "All restaurants", "1h", now_utc=now)
    assert len(filtered) == 1
    assert filtered.iloc[0]["window_end"] == datetime(2026, 4, 1, 9, 55, tzinfo=UTC)


def test_apply_overview_filters_supports_24h_window():
    now = datetime(2026, 4, 2, 12, 0, tzinfo=UTC)
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 11, 30, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 11, 45, tzinfo=UTC),
                "active_orders": 3,
                "avg_delivery_time_seconds": 610.0,
                "cancellation_rate": 0.04,
            },
            {
                "zone_id": "zone-2",
                "restaurant_id": "rest-3",
                "window_start": datetime(2026, 4, 1, 12, 5, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 12, 20, tzinfo=UTC),
                "active_orders": 5,
                "avg_delivery_time_seconds": 590.0,
                "cancellation_rate": 0.06,
            },
        ]
    )

    filtered = apply_overview_filters(frame, "All zones", "All restaurants", "24h", now_utc=now)
    assert len(filtered) == 1
    assert filtered.iloc[0]["zone_id"] == "zone-2"


def test_format_active_filters_lists_all_dimensions():
    summary = format_active_filters("zone-1", "rest-2", "24h")
    assert summary == "Active filters - Zone: zone-1, Restaurant: rest-2, Time window: 24h"


def test_normalize_window_presets_keeps_valid_unique_values():
    presets = _normalize_window_presets(["15m", "1h", "15m", "24h"], "1h")
    assert presets == ["15m", "1h", "24h"]


def test_normalize_window_presets_ignores_invalid_values_without_raising():
    with pytest.warns(UserWarning, match="Ignoring invalid dashboard time-window preset"):
        presets = _normalize_window_presets(["15m", "bad", "0h", " ", "1h"], "not-valid")
    assert presets == ["15m", "1h"]


def test_run_shows_no_data_message_after_filters(monkeypatch):
    now = datetime(2026, 4, 1, 10, 15, tzinfo=UTC)
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 9, 15, tzinfo=UTC),
                "active_orders": 1,
                "avg_delivery_time_seconds": 700.0,
                "cancellation_rate": 0.1,
            }
        ]
    )

    class FakeColumn:
        def __init__(self, value):
            self._value = value

        def selectbox(self, *_args, **_kwargs):
            return self._value

        def metric(self, *_args, **_kwargs):
            pass

    class FakeSpinner:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}
            self.info_messages = []

        def set_page_config(self, **_kwargs):
            pass

        def title(self, *_args, **_kwargs):
            pass

        def caption(self, *_args, **_kwargs):
            pass

        def toggle(self, *_args, **_kwargs):
            return False

        def spinner(self, *_args, **_kwargs):
            return FakeSpinner()

        def columns(self, _count):
            return [FakeColumn("zone-2"), FakeColumn("All restaurants"), FakeColumn("15m")]

        def info(self, message):
            self.info_messages.append(message)

        def subheader(self, *_args, **_kwargs):
            pass

        def line_chart(self, *_args, **_kwargs):
            pass

        def error(self, *_args, **_kwargs):
            raise AssertionError("run() should not hit error path in this test")

    fake_st = FakeStreamlit()
    cache = MetricsCache(ttl_seconds=15.0, now_fn=lambda: 0.0)
    cache._cached_value = frame
    cache._cached_at = 0.0
    fake_st.session_state["_overview_metrics_cache"] = cache

    monkeypatch.setattr("stream_analytics.dashboard.app._import_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        "stream_analytics.dashboard.app.load_dashboard_config",
        lambda: DashboardConfig(
            metrics_path="ignored",
            refresh_seconds=15,
            time_window_presets=["15m", "1h", "24h"],
            default_time_window="15m",
        ),
    )
    monkeypatch.setattr("stream_analytics.dashboard.app.datetime", type("FakeDateTime", (), {"now": staticmethod(lambda _tz: now)}))

    run()

    assert "No matching data for the current zone, restaurant, and time-window filters." in fake_st.info_messages


def test_apply_overview_filters_meets_dashboard_responsiveness_target():
    now = datetime(2026, 4, 2, 12, 0, tzinfo=UTC)
    rows = []
    for i in range(50000):
        minute = i % 120
        rows.append(
            {
                "zone_id": f"zone-{i % 10}",
                "restaurant_id": f"rest-{i % 50}",
                "window_start": datetime(2026, 4, 2, 10, minute % 60, tzinfo=UTC),
                "window_end": datetime(2026, 4, 2, 11, minute % 60, tzinfo=UTC),
                "active_orders": (i % 7) + 1,
                "avg_delivery_time_seconds": 450.0 + (i % 300),
                "cancellation_rate": (i % 15) / 100.0,
            }
        )
    frame = pd.DataFrame(rows)

    start = time.perf_counter()
    filtered = apply_overview_filters(frame, "zone-3", "rest-13", "1h", now_utc=now)
    elapsed = time.perf_counter() - start

    assert elapsed < 3.0
    assert not filtered.empty
