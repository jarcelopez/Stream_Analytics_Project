from __future__ import annotations

from stream_analytics.spark_jobs.anomaly_scores import compute_zone_stress_values
from stream_analytics.spark_jobs.windowed_kpis import compute_windowed_kpi_rows


def test_compute_windowed_kpi_rows_includes_core_and_intermediate_metrics():
    base = 1_700_000_000_000_000
    rows = compute_windowed_kpi_rows(
        order_events=[
            {
                "event_time": base,
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "order_id": "order-1",
                "status": "CREATED",
                "delivery_time_seconds": None,
            },
            {
                "event_time": base + 30_000_000,
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "order_id": "order-1",
                "status": "DELIVERED",
                "delivery_time_seconds": 900.0,
            },
            {
                "event_time": base + 60_000_000,
                "zone_id": "zone-1",
                "restaurant_id": "rest-1",
                "order_id": "order-2",
                "status": "CANCELLED",
                "delivery_time_seconds": None,
            },
        ],
        courier_status=[
            {"event_time": base, "zone_id": "zone-1", "courier_id": "courier-1", "status": "ONLINE"},
            {"event_time": base + 1_000_000, "zone_id": "zone-1", "courier_id": "courier-2", "status": "OFFLINE"},
        ],
        window_duration_seconds=600,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["zone_id"] == "zone-1"
    assert row["restaurant_id"] == "rest-1"
    assert row["total_orders"] == 2
    assert row["active_orders"] == 1
    assert row["avg_delivery_time_seconds"] == 900.0
    assert row["cancellation_rate"] == 0.5
    assert row["active_couriers"] == 1
    assert row["orders_per_active_courier"] == 2.0


def test_compute_zone_stress_values_generates_expected_scoring_fields():
    row = compute_zone_stress_values(
        cancellation_rate=0.5,
        avg_delivery_time_seconds=1800.0,
        orders_per_active_courier=4.0,
        stress_index_threshold=0.75,
    )
    assert row["delivery_time_ratio"] == 1.0
    assert row["zone_stress_index"] == 0.8
    assert row["stress_threshold"] == 0.75
    assert row["is_stressed"] is True


def test_compute_zone_stress_values_handles_missing_inputs_deterministically():
    row = compute_zone_stress_values(
        cancellation_rate=0.0,
        avg_delivery_time_seconds=None,
        orders_per_active_courier=None,
        stress_index_threshold=0.30,
    )
    assert row["delivery_time_ratio"] == 0.0
    assert row["zone_stress_index"] == 0.25
    assert row["is_stressed"] is False
