from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from stream_analytics.dashboard.app import (
    build_kpi_snapshot,
    prepare_time_series,
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
