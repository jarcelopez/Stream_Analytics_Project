from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from stream_analytics.dashboard.app import (
    MetricsCache,
    _schedule_rerun,
    load_metrics_dataset,
)


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "window_start": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "window_end": datetime(2026, 4, 1, 10, 10, tzinfo=UTC),
                "active_orders": 4,
                "avg_delivery_time_seconds": 600.0,
                "cancellation_rate": 0.25,
            }
        ]
    )


def test_load_metrics_dataset_returns_empty_frame_for_missing_dataset(tmp_path):
    missing = tmp_path / "not-there"
    frame = load_metrics_dataset(str(missing))
    assert frame.empty


def test_load_metrics_dataset_rejects_malformed_columns(tmp_path):
    dataset_path = tmp_path / "metrics"
    dataset_path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"zone_id": "zone-1"}]).to_parquet(dataset_path / "part-1.parquet")

    with pytest.raises(ValueError):
        load_metrics_dataset(str(dataset_path))


def test_metrics_cache_refreshes_after_ttl_expiry():
    values = [1, 2]
    calls = {"count": 0}
    clock = {"time": 100.0}

    def loader() -> pd.DataFrame:
        idx = calls["count"]
        calls["count"] += 1
        return pd.DataFrame({"value": [values[idx]]})

    cache = MetricsCache(ttl_seconds=5.0, now_fn=lambda: clock["time"])
    first = cache.get(loader)
    second = cache.get(loader)
    clock["time"] = 106.0
    third = cache.get(loader)

    assert first["value"].iloc[0] == 1
    assert second["value"].iloc[0] == 1
    assert third["value"].iloc[0] == 2
    assert calls["count"] == 2


def test_load_metrics_dataset_reads_valid_parquet(tmp_path):
    dataset_path = tmp_path / "metrics"
    dataset_path.mkdir(parents=True, exist_ok=True)
    _valid_frame().to_parquet(dataset_path / "part-1.parquet")

    frame = load_metrics_dataset(str(dataset_path))
    assert not frame.empty
    assert "window_start" in frame.columns


def test_schedule_rerun_triggers_when_interval_elapsed():
    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}
            self.rerun_called = False

        def rerun(self):
            self.rerun_called = True

    st = FakeStreamlit()
    _schedule_rerun(st=st, refresh_seconds=5)
    st.session_state["_overview_next_refresh_at"] = -1
    _schedule_rerun(st=st, refresh_seconds=5)

    assert st.rerun_called is True
    assert "_overview_next_refresh_at" in st.session_state
