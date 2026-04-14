from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from stream_analytics.spark_jobs.parquet_inspection import (
    METRICS_DATASET_NAME,
    REQUIRED_METRICS_COLUMNS,
    assert_required_columns,
    read_parquet_records,
    validate_metrics_row,
)
from stream_analytics.spark_jobs import inspect_curated_parquet as inspect_cli


def _base_row() -> dict:
    return {
        "zone_id": "zone-1",
        "restaurant_id": "rest-1",
        "window_start": datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
        "window_end": datetime(2026, 4, 1, 12, 10, tzinfo=timezone.utc),
        "active_orders": 3,
        "avg_delivery_time_seconds": 850.0,
        "cancellation_rate": 0.25,
        "total_orders": 4,
        "active_couriers": 2,
        "orders_per_active_courier": 2.0,
        "delivery_time_ratio": 0.45,
        "zone_stress_index": 0.38,
        "stress_threshold": 0.75,
        "is_stressed": False,
    }


def test_required_columns_remain_story_3_4_compatible():
    columns = set(REQUIRED_METRICS_COLUMNS)
    assert "zone_stress_index" in columns
    assert "delivery_time_ratio" in columns
    assert "is_stressed" in columns
    assert METRICS_DATASET_NAME == "metrics_by_zone_restaurant_window"
    assert_required_columns(columns)


def test_validate_metrics_row_accepts_valid_payload():
    errors = validate_metrics_row(_base_row())
    assert errors == []


def test_validate_metrics_row_rejects_negative_and_out_of_range_values():
    row = _base_row()
    row["active_orders"] = -1
    row["cancellation_rate"] = 1.1
    row["zone_stress_index"] = -0.2
    errors = validate_metrics_row(row)
    assert any("active_orders" in item for item in errors)
    assert any("cancellation_rate" in item for item in errors)
    assert any("zone_stress_index" in item for item in errors)


def test_assert_required_columns_fails_when_contract_is_broken():
    with pytest.raises(ValueError):
        assert_required_columns({"zone_id", "restaurant_id"})


def test_read_parquet_records_reads_local_path_with_pandas(monkeypatch, tmp_path):
    dataset_dir = tmp_path / "metrics_dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    called = {}

    class FakeFrame:
        def head(self, limit):
            called["limit"] = limit
            return self

        def to_dict(self, orient):
            called["orient"] = orient
            return [{"zone_id": "zone-1"}]

    def fake_read_parquet(path):
        called["path"] = path
        return FakeFrame()

    monkeypatch.setitem(
        __import__("sys").modules,
        "pandas",
        SimpleNamespace(read_parquet=fake_read_parquet),
    )
    records = read_parquet_records(str(dataset_dir), limit=3)
    assert records == [{"zone_id": "zone-1"}]
    assert called["path"] == str(dataset_dir)
    assert called["limit"] == 3
    assert called["orient"] == "records"


def test_read_parquet_records_allows_remote_uri_without_local_exists(monkeypatch):
    called = {}

    class FakeFrame:
        def head(self, limit):
            called["limit"] = limit
            return self

        def to_dict(self, orient):
            called["orient"] = orient
            return [{"zone_id": "zone-1"}]

    def fake_read_parquet(path):
        called["path"] = path
        return FakeFrame()

    monkeypatch.setitem(
        __import__("sys").modules,
        "pandas",
        SimpleNamespace(read_parquet=fake_read_parquet),
    )
    uri = "abfss://demo@storage.dfs.core.windows.net/data/metrics_by_zone_restaurant_window"
    records = read_parquet_records(uri, limit=2)
    assert records == [{"zone_id": "zone-1"}]
    assert called["path"] == uri
    assert called["limit"] == 2
    assert called["orient"] == "records"


def test_read_parquet_records_missing_local_path_raises():
    with pytest.raises(FileNotFoundError):
        read_parquet_records("does-not-exist/metrics")


def test_inspect_curated_parquet_cli_handles_empty_dataset(monkeypatch, capsys):
    monkeypatch.setattr(inspect_cli, "read_parquet_records", lambda path, limit: [])
    monkeypatch.setattr(__import__("sys"), "argv", ["inspect_curated_parquet", "--path", "data/metrics", "--limit", "2"])
    code = inspect_cli.main()
    out = capsys.readouterr().out
    assert code == 0
    assert "No rows found in parquet dataset." in out
    assert "FROM parquet.`data/metrics`" in out
