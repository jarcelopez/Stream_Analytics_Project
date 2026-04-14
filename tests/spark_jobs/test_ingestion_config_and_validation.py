from __future__ import annotations

import json
from pathlib import Path

import pytest

from stream_analytics.spark_jobs.config_models import SparkIngestionConfig
from stream_analytics.spark_jobs import ingestion as ingestion_mod
from stream_analytics.spark_jobs.ingestion import (
    _extract_namespace,
    build_eventhub_source_options,
    create_eventhub_source_df,
    load_ingestion_config,
    parse_and_validate_record,
    run_ingestion_streaming_job,
    run_ingestion_sample,
    split_valid_invalid_records,
)
from stream_analytics.spark_jobs.windowing import summarize_late_event_handling


def test_load_ingestion_config_requires_connection_string(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config"
    cfg_path.mkdir(parents=True, exist_ok=True)
    (cfg_path / "spark_jobs.yaml").write_text(
        "\n".join(
            [
                "order_event_hub_name: order-events",
                "courier_event_hub_name: courier-status",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))
    monkeypatch.delenv("SPARK_EVENTHUB_CONNECTION_STRING", raising=False)

    with pytest.raises(ValueError):
        load_ingestion_config()


def test_load_ingestion_config_with_env_override(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config"
    cfg_path.mkdir(parents=True, exist_ok=True)
    (cfg_path / "spark_jobs.yaml").write_text(
        "\n".join(
            [
                "order_event_hub_name: order-events",
                "courier_event_hub_name: courier-status",
                "starting_position: latest",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))
    monkeypatch.setenv(
        "SPARK_EVENTHUB_CONNECTION_STRING",
        "Endpoint=sb://my-ns.servicebus.windows.net/;SharedAccessKeyName=policy;SharedAccessKey=secret",
    )
    monkeypatch.setenv("SPARK_JOBS_ORDER_EVENT_HUB_NAME", "custom-orders")

    cfg = load_ingestion_config()
    assert isinstance(cfg, SparkIngestionConfig)
    assert cfg.order_event_hub_name == "custom-orders"


def test_build_eventhub_source_options():
    conn = "Endpoint=sb://my-ns.servicebus.windows.net/;SharedAccessKeyName=policy;SharedAccessKey=secret"
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SPARK_EVENTHUB_CONNECTION_STRING", conn)
        options = build_eventhub_source_options(
            hub_name="order-events",
            consumer_group="$Default",
            starting_position="latest",
        )
    assert options["subscribe"] == "order-events"
    assert options["startingOffsets"] == "latest"
    assert options["kafka.bootstrap.servers"] == "my-ns.servicebus.windows.net:9093"


def test_parse_and_validate_record_success():
    payload = {
        "feed_type": "order_events",
        "event_time": 1700000000000000,
        "order_id": "order-1",
        "restaurant_id": "rest-1",
        "courier_id": "courier-1",
        "zone_id": "zone-1",
    }
    valid, error = parse_and_validate_record(json.dumps(payload), "order_events")
    assert valid is not None
    assert error is None


def test_parse_and_validate_record_routes_invalid():
    valid, error = parse_and_validate_record("{bad json", "order_events")
    assert valid is None
    assert error is not None
    assert error["details"]["reason_code"] == "parse_error"


def test_split_valid_invalid_records():
    records = [
        json.dumps(
            {
                "feed_type": "courier_status",
                "event_time": 1700000000000000,
                "courier_id": "courier-1",
                "zone_id": "zone-1",
            }
        ),
        json.dumps(
            {
                "feed_type": "courier_status",
                "event_time": "invalid",
                "courier_id": "courier-2",
                "zone_id": "zone-2",
            }
        ),
    ]
    valids, invalids = split_valid_invalid_records(records, "courier_status")
    assert len(valids) == 1
    assert len(invalids) == 1
    assert invalids[0]["details"]["reason_code"] == "invalid_timestamp"


def test_run_ingestion_sample_writes_status_and_error_sink(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "spark_jobs.yaml").write_text(
        "\n".join(
            [
                "order_event_hub_name: order-events",
                "courier_event_hub_name: courier-status",
                f"error_sink_path: {str((tmp_path / 'logs' / 'errors.jsonl')).replace(chr(92), '/')}",
                "checkpoint_base_dir: checkpoints/spark_jobs",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "SPARK_EVENTHUB_CONNECTION_STRING",
        "Endpoint=sb://my-ns.servicebus.windows.net/;SharedAccessKeyName=policy;SharedAccessKey=secret",
    )

    counts = run_ingestion_sample(
        raw_order_records=[
            json.dumps(
                {
                    "feed_type": "order_events",
                    "event_time": 1700000000000000,
                    "order_id": "order-1",
                    "restaurant_id": "rest-1",
                    "courier_id": "courier-1",
                    "zone_id": "zone-1",
                }
            ),
            '{"feed_type":"order_events","event_time":"oops"}',
        ],
        raw_courier_records=[],
        debug_mode=True,
    )

    assert counts["order_valid_count"] == 1
    assert counts["order_invalid_count"] == 1
    assert (tmp_path / "status" / "spark_job_status.json").exists()
    assert (tmp_path / "logs" / "errors.jsonl").exists()


def test_extract_namespace_from_connection_string():
    conn = "Endpoint=sb://demo-namespace.servicebus.windows.net/;SharedAccessKeyName=policy;SharedAccessKey=secret"
    assert _extract_namespace(conn) == "demo-namespace"


def test_create_eventhub_source_df_uses_kafka_readstream():
    class FakeReader:
        def __init__(self):
            self.format_name = None
            self.options_map = {}

        def format(self, format_name):
            self.format_name = format_name
            return self

        def options(self, **kwargs):
            self.options_map = kwargs
            return self

        def load(self):
            return {"loaded": True, "options": self.options_map}

    class FakeSpark:
        def __init__(self):
            self.readStream = FakeReader()

    conn = "Endpoint=sb://my-ns.servicebus.windows.net/;SharedAccessKeyName=policy;SharedAccessKey=secret"
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SPARK_EVENTHUB_CONNECTION_STRING", conn)
        spark = FakeSpark()
        source_df = create_eventhub_source_df(
            spark,
            hub_name="order-events",
            consumer_group="$Default",
            starting_position="earliest",
        )

    assert spark.readStream.format_name == "kafka"
    assert source_df["loaded"] is True
    assert source_df["options"]["subscribe"] == "order-events"
    assert source_df["options"]["startingOffsets"] == "earliest"


def test_run_ingestion_sample_sets_error_status_on_failure(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "spark_jobs.yaml").write_text(
        "\n".join(
            [
                "order_event_hub_name: order-events",
                "courier_event_hub_name: courier-status",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTEST_PROJECT_ROOT_OVERRIDE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(
        "SPARK_EVENTHUB_CONNECTION_STRING",
        "Endpoint=sb://my-ns.servicebus.windows.net/;SharedAccessKeyName=policy;SharedAccessKey=secret",
    )
    monkeypatch.setattr(ingestion_mod, "write_error_sink", lambda errors, sink_path: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError):
        run_ingestion_sample(
            raw_order_records=['{"feed_type":"order_events","event_time":"oops"}'],
            raw_courier_records=[],
            debug_mode=False,
        )

    status_payload = json.loads((tmp_path / "status" / "spark_job_status.json").read_text(encoding="utf-8"))
    assert status_payload["status"] == "ERROR"


def test_run_ingestion_streaming_job_writes_error_on_failure(monkeypatch):
    fake_cfg = SparkIngestionConfig(
        order_event_hub_name="order-events",
        courier_event_hub_name="courier-status",
        consumer_group="$Default",
        starting_position="latest",
        checkpoint_base_dir="checkpoints/spark_jobs",
        error_sink_path="logs/spark_ingestion_errors.jsonl",
    )
    statuses = []
    timezone_sets = []

    class FakeConf:
        def set(self, key, value):
            timezone_sets.append((key, value))

    class FakeSpark:
        conf = FakeConf()

    monkeypatch.setattr(ingestion_mod, "load_ingestion_config", lambda: fake_cfg)
    monkeypatch.setattr(ingestion_mod, "write_status", lambda status, **kwargs: statuses.append(status))
    monkeypatch.setattr(
        ingestion_mod,
        "create_eventhub_source_df",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("source-failure")),
    )

    with pytest.raises(RuntimeError):
        run_ingestion_streaming_job(FakeSpark(), debug_mode=False)

    assert statuses == ["RUNNING", "ERROR"]
    assert timezone_sets == [("spark.sql.session.timeZone", "UTC")]


def test_query_dropped_by_watermark_rows_reads_progress_metrics():
    class FakeQuery:
        def __init__(self, name, last_progress):
            self.name = name
            self.lastProgress = last_progress

    class FakeStreams:
        def __init__(self, active):
            self.active = active

    class FakeSpark:
        def __init__(self, active):
            self.streams = FakeStreams(active)

    spark = FakeSpark(
        [
            FakeQuery("not_me", {"stateOperators": [{"numRowsDroppedByWatermark": 2}]}),
            FakeQuery(
                "order_events_windowed_kpis",
                {"stateOperators": [{"numRowsDroppedByWatermark": 3}, {"numRowsDroppedByWatermark": 4}]},
            ),
        ]
    )

    value = ingestion_mod._query_dropped_by_watermark_rows(spark, "order_events_windowed_kpis")
    assert value == 7


def test_spark_ingestion_config_rejects_invalid_window_duration_strings():
    with pytest.raises(ValueError):
        SparkIngestionConfig(
            order_event_hub_name="order-events",
            courier_event_hub_name="courier-status",
            watermark_delay="ten minutes",
            window_duration="10 minutes",
            window_slide="5 minutes",
        )


def test_spark_ingestion_config_rejects_slide_greater_than_window():
    with pytest.raises(ValueError):
        SparkIngestionConfig(
            order_event_hub_name="order-events",
            courier_event_hub_name="courier-status",
            watermark_delay="10 minutes",
            window_duration="10 minutes",
            window_slide="11 minutes",
        )


def test_summarize_late_event_handling_includes_and_drops_by_watermark_boundary():
    max_event_time = 2_000_000_000
    accepted_late = max_event_time - (5 * 60 * 1_000_000)  # within 10-minute delay
    too_late = max_event_time - (11 * 60 * 1_000_000)  # beyond 10-minute delay
    summary = summarize_late_event_handling(
        [max_event_time, accepted_late, too_late],
        watermark_delay="10 minutes",
        window_duration="10 minutes",
    )

    assert summary["accepted_records"] == 2
    assert summary["accepted_late_records"] == 1
    assert summary["too_late_dropped_records"] == 1
    assert summary["watermark_micros"] == max_event_time - (10 * 60 * 1_000_000)

