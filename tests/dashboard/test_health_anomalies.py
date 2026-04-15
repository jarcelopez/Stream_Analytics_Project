from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from stream_analytics.dashboard.app import (
    DashboardConfig,
    _render_health_page,
    apply_health_filters,
    format_health_active_filters,
)


def _build_health_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "anomaly_score": 0.91,
                "zone_stress_index": 0.70,
            },
            {
                "zone_id": "zone-2",
                "window_start": datetime(2026, 4, 1, 10, 5, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 15, tzinfo=UTC),
                "anomaly_score": 0.81,
                "zone_stress_index": 0.90,
            },
            {
                "zone_id": "zone-3",
                "window_start": datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 9, 10, tzinfo=UTC),
                "anomaly_score": 0.88,
                "zone_stress_index": 0.89,
            },
        ]
    )


def test_apply_health_filters_sorts_by_severity_and_limits_top_n():
    frame = _build_health_frame()

    ranked = apply_health_filters(
        frame,
        selected_zone="All zones",
        selected_window="1h",
        threshold=0.80,
        top_n=1,
        fallback_score_column="cancellation_rate",
        now_utc=datetime(2026, 4, 1, 10, 20, tzinfo=UTC),
    )

    assert len(ranked) == 2
    assert set(ranked["zone_id"]) == {"zone-1", "zone-2"}
    assert ranked.iloc[0]["severity_score"] == 0.81


def test_apply_health_filters_handles_zone_and_time_window_filters():
    frame = _build_health_frame()

    ranked = apply_health_filters(
        frame,
        selected_zone="zone-2",
        selected_window="15m",
        threshold=0.50,
        top_n=10,
        fallback_score_column="cancellation_rate",
        now_utc=datetime(2026, 4, 1, 10, 20, tzinfo=UTC),
    )

    assert len(ranked) == 1
    assert ranked.iloc[0]["zone_id"] == "zone-2"


def test_apply_health_filters_uses_fallback_score_column_when_needed():
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-9",
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "cancellation_rate": 0.45,
            }
        ]
    )

    ranked = apply_health_filters(
        frame,
        selected_zone="All zones",
        selected_window="1h",
        threshold=0.40,
        top_n=10,
        fallback_score_column="cancellation_rate",
        now_utc=datetime(2026, 4, 1, 10, 20, tzinfo=UTC),
    )

    assert len(ranked) == 1
    assert ranked.iloc[0]["severity_score"] == 0.45


def test_apply_health_filters_returns_empty_for_threshold_miss():
    frame = _build_health_frame()

    ranked = apply_health_filters(
        frame,
        selected_zone="All zones",
        selected_window="1h",
        threshold=0.95,
        top_n=10,
        fallback_score_column="cancellation_rate",
        now_utc=datetime(2026, 4, 1, 10, 20, tzinfo=UTC),
    )

    assert ranked.empty


def test_format_health_active_filters_is_human_readable():
    summary = format_health_active_filters("zone-1", "1h", 0.8, 5)
    assert summary == "Active filters - Zone: zone-1, Time window: 1h, Threshold: >= 0.80, Top N: 5"


def test_apply_health_filters_limits_top_n_per_time_window():
    frame = pd.DataFrame(
        [
            {
                "zone_id": "zone-a",
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "anomaly_score": 0.95,
            },
            {
                "zone_id": "zone-b",
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "anomaly_score": 0.90,
            },
            {
                "zone_id": "zone-c",
                "window_start": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 20, tzinfo=UTC),
                "anomaly_score": 0.92,
            },
            {
                "zone_id": "zone-d",
                "window_start": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 20, tzinfo=UTC),
                "anomaly_score": 0.89,
            },
        ]
    )

    ranked = apply_health_filters(
        frame,
        selected_zone="All zones",
        selected_window="1h",
        threshold=0.80,
        top_n=1,
        fallback_score_column="cancellation_rate",
        now_utc=datetime(2026, 4, 1, 10, 30, tzinfo=UTC),
    )

    assert len(ranked) == 2
    assert set(ranked["zone_id"]) == {"zone-a", "zone-c"}


def test_render_health_page_shows_empty_state_message_when_threshold_filters_everything():
    class FakeColumn:
        def __init__(self, value):
            self._value = value

        def selectbox(self, *_args, **_kwargs):
            return self._value

        def slider(self, *_args, **_kwargs):
            return self._value

        def number_input(self, *_args, **_kwargs):
            return self._value

    class FakeStreamlit:
        def __init__(self):
            self.info_messages = []

        def subheader(self, *_args, **_kwargs):
            pass

        def columns(self, _count):
            return [
                FakeColumn("All zones"),
                FakeColumn("1h"),
                FakeColumn(0.99),
                FakeColumn(10),
            ]

        def caption(self, *_args, **_kwargs):
            pass

        def info(self, message):
            self.info_messages.append(message)

        def dataframe(self, *_args, **_kwargs):
            raise AssertionError("dataframe should not render when ranked results are empty")

    fake_st = FakeStreamlit()
    _render_health_page(
        st=fake_st,
        frame=_build_health_frame(),
        config=DashboardConfig(),
        auto_refresh=False,
    )
    assert (
        "No stressed or anomalous zones exceeded the configured threshold for the current filters."
        in fake_st.info_messages
    )
