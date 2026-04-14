from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from stream_analytics.common.config import load_typed_config
from stream_analytics.common.logging_utils import log_error, log_info
from stream_analytics.spark_jobs.config_models import SparkIngestionConfig

_COMPONENT = "spark_ingestion"
_SPARK_CONFIG_PATH = "config/spark_jobs.yaml"
_REQUIRED_CONN_ENV = "SPARK_EVENTHUB_CONNECTION_STRING"

_REASON_PARSE_ERROR = "parse_error"
_REASON_SCHEMA_MISMATCH = "schema_mismatch"
_REASON_MISSING_FIELD = "missing_field"
_REASON_INVALID_TIMESTAMP = "invalid_timestamp"
_REASON_INVALID_FEED = "invalid_feed_type"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Required environment variable '{name}' is missing.")
    return value


def load_ingestion_config() -> SparkIngestionConfig:
    try:
        cfg: SparkIngestionConfig = load_typed_config(
            relative_yaml_path=_SPARK_CONFIG_PATH,
            model_type=SparkIngestionConfig,
            env_prefix="SPARK_JOBS_",
        )
        _require_env(_REQUIRED_CONN_ENV)
        return cfg
    except Exception as exc:
        log_error(
            _COMPONENT,
            "Failed to load Spark ingestion configuration",
            {"error": str(exc), "config_path": _SPARK_CONFIG_PATH},
        )
        raise


def build_eventhub_source_options(
    *,
    hub_name: str,
    consumer_group: str,
    starting_position: str,
) -> Dict[str, str]:
    conn = _require_env(_REQUIRED_CONN_ENV)
    if starting_position not in {"latest", "earliest"}:
        raise ValueError("starting_position must be 'latest' or 'earliest'")
    return {
        "kafka.bootstrap.servers": f"{_extract_namespace(conn)}.servicebus.windows.net:9093",
        "kafka.security.protocol": "SASL_SSL",
        "kafka.sasl.mechanism": "PLAIN",
        "kafka.sasl.jaas.config": (
            'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule '
            f'required username="$ConnectionString" password="{conn}";'
        ),
        "subscribe": hub_name,
        "startingOffsets": "latest" if starting_position == "latest" else "earliest",
        "kafka.group.id": consumer_group,
        "failOnDataLoss": "false",
    }


def create_eventhub_source_df(
    spark: Any,
    *,
    hub_name: str,
    consumer_group: str,
    starting_position: str,
) -> Any:
    """
    Build a Spark Structured Streaming source DataFrame for Event Hubs via Kafka endpoint.
    """
    options = build_eventhub_source_options(
        hub_name=hub_name,
        consumer_group=consumer_group,
        starting_position=starting_position,
    )
    return spark.readStream.format("kafka").options(**options).load()


def build_valid_invalid_dataframes(source_df: Any, *, expected_feed_type: str) -> Tuple[Any, Any]:
    """
    Parse Kafka payloads into typed Spark DataFrames and split valid/invalid records.
    """
    try:
        from pyspark.sql import functions as F
        from pyspark.sql.types import LongType, StringType, StructField, StructType
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "pyspark is required for structured streaming ingestion. Install pyspark to run Spark ingestion jobs."
        ) from exc

    schema_fields: List[StructField] = [
        StructField("feed_type", StringType(), True),
        StructField("event_time", LongType(), True),
        StructField("zone_id", StringType(), True),
    ]
    if expected_feed_type == "order_events":
        schema_fields.extend(
            [
                StructField("order_id", StringType(), True),
                StructField("restaurant_id", StringType(), True),
                StructField("courier_id", StringType(), True),
            ]
        )
    else:
        schema_fields.append(StructField("courier_id", StringType(), True))

    payload_schema = StructType(schema_fields)

    parsed_df = source_df.selectExpr("CAST(value AS STRING) AS raw_payload").withColumn(
        "parsed_payload",
        F.from_json(F.col("raw_payload"), payload_schema),
    )

    reason_code = (
        F.when(F.col("parsed_payload").isNull(), F.lit(_REASON_SCHEMA_MISMATCH))
        .when(F.col("parsed_payload.feed_type").isNull(), F.lit(_REASON_MISSING_FIELD))
        .when(F.col("parsed_payload.feed_type") != F.lit(expected_feed_type), F.lit(_REASON_INVALID_FEED))
        .when(F.col("parsed_payload.event_time").isNull(), F.lit(_REASON_INVALID_TIMESTAMP))
    )
    if expected_feed_type == "order_events":
        reason_code = reason_code.when(
            F.col("parsed_payload.order_id").isNull()
            | (F.trim(F.col("parsed_payload.order_id")) == F.lit(""))
            | F.col("parsed_payload.restaurant_id").isNull()
            | (F.trim(F.col("parsed_payload.restaurant_id")) == F.lit(""))
            | F.col("parsed_payload.courier_id").isNull()
            | (F.trim(F.col("parsed_payload.courier_id")) == F.lit(""))
            | F.col("parsed_payload.zone_id").isNull()
            | (F.trim(F.col("parsed_payload.zone_id")) == F.lit("")),
            F.lit(_REASON_MISSING_FIELD),
        )
    else:
        reason_code = reason_code.when(
            F.col("parsed_payload.courier_id").isNull()
            | (F.trim(F.col("parsed_payload.courier_id")) == F.lit(""))
            | F.col("parsed_payload.zone_id").isNull()
            | (F.trim(F.col("parsed_payload.zone_id")) == F.lit("")),
            F.lit(_REASON_MISSING_FIELD),
        )

    classified_df = parsed_df.withColumn("reason_code", reason_code)
    valid_df = classified_df.where(F.col("reason_code").isNull()).select("parsed_payload.*")
    invalid_df = (
        classified_df.where(F.col("reason_code").isNotNull())
        .select(
            F.current_timestamp().alias("timestamp"),
            F.lit(_COMPONENT).alias("component"),
            F.lit("ERROR").alias("level"),
            F.lit("invalid event routed to error sink").alias("message"),
            F.to_json(
                F.struct(
                    F.col("reason_code").alias("reason_code"),
                    F.lit(expected_feed_type).alias("expected_feed_type"),
                    F.col("raw_payload").alias("payload"),
                )
            ).alias("details"),
        )
    )
    return valid_df, invalid_df


def run_ingestion_streaming_job(spark: Any, *, debug_mode: bool = False) -> Dict[str, Any]:
    """
    Start Spark Structured Streaming ingestion queries for both configured feeds.
    """
    cfg = load_ingestion_config()
    try:
        write_status("RUNNING", debug_mode=debug_mode)
        order_source = create_eventhub_source_df(
            spark,
            hub_name=cfg.order_event_hub_name,
            consumer_group=cfg.consumer_group,
            starting_position=cfg.starting_position,
        )
        courier_source = create_eventhub_source_df(
            spark,
            hub_name=cfg.courier_event_hub_name,
            consumer_group=cfg.consumer_group,
            starting_position=cfg.starting_position,
        )

        order_valid_df, order_invalid_df = build_valid_invalid_dataframes(order_source, expected_feed_type="order_events")
        courier_valid_df, courier_invalid_df = build_valid_invalid_dataframes(
            courier_source,
            expected_feed_type="courier_status",
        )

        order_valid_query = (
            order_valid_df.writeStream.outputMode("append")
            .format("memory")
            .queryName("order_events_valid")
            .option("checkpointLocation", f"{cfg.checkpoint_base_dir}/order_events_valid")
            .start()
        )
        courier_valid_query = (
            courier_valid_df.writeStream.outputMode("append")
            .format("memory")
            .queryName("courier_status_valid")
            .option("checkpointLocation", f"{cfg.checkpoint_base_dir}/courier_status_valid")
            .start()
        )
        error_query = (
            order_invalid_df.unionByName(courier_invalid_df).writeStream.outputMode("append")
            .format("json")
            .option("path", cfg.error_sink_path)
            .option("checkpointLocation", f"{cfg.checkpoint_base_dir}/error_sink")
            .start()
        )

        log_info(
            _COMPONENT,
            "streaming ingestion queries started",
            {
                "order_event_hub_name": cfg.order_event_hub_name,
                "courier_event_hub_name": cfg.courier_event_hub_name,
                "checkpoint_base_dir": cfg.checkpoint_base_dir,
                "error_sink_path": cfg.error_sink_path,
            },
        )
        return {
            "order_valid_query": order_valid_query,
            "courier_valid_query": courier_valid_query,
            "error_query": error_query,
        }
    except Exception:
        write_status("ERROR", debug_mode=debug_mode)
        raise


def parse_and_validate_record(raw_json: str, expected_feed_type: str) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
    try:
        payload = json.loads(raw_json)
    except Exception:
        return None, _error_record(_REASON_PARSE_ERROR, expected_feed_type, raw_json, "payload is not valid JSON")

    if not isinstance(payload, dict):
        return None, _error_record(_REASON_SCHEMA_MISMATCH, expected_feed_type, raw_json, "payload root is not an object")

    missing_keys = [k for k in ("event_time", "feed_type") if k not in payload]
    if missing_keys:
        return None, _error_record(_REASON_MISSING_FIELD, expected_feed_type, raw_json, f"missing required fields: {missing_keys}")

    if payload.get("feed_type") != expected_feed_type:
        return None, _error_record(
            _REASON_INVALID_FEED,
            expected_feed_type,
            raw_json,
            f"expected feed_type '{expected_feed_type}', got '{payload.get('feed_type')}'",
        )

    if not isinstance(payload.get("event_time"), int):
        return None, _error_record(_REASON_INVALID_TIMESTAMP, expected_feed_type, raw_json, "event_time must be int micros")

    required_ids = {
        "order_events": ("order_id", "restaurant_id", "courier_id", "zone_id"),
        "courier_status": ("courier_id", "zone_id"),
    }[expected_feed_type]
    missing_ids = [k for k in required_ids if not str(payload.get(k, "")).strip()]
    if missing_ids:
        return None, _error_record(_REASON_MISSING_FIELD, expected_feed_type, raw_json, f"missing id fields: {missing_ids}")

    return payload, None


def split_valid_invalid_records(raw_records: Iterable[str], expected_feed_type: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    valids: List[Dict[str, Any]] = []
    invalids: List[Dict[str, Any]] = []
    for raw_json in raw_records:
        valid, error = parse_and_validate_record(raw_json, expected_feed_type)
        if valid is not None:
            valids.append(valid)
        else:
            assert error is not None
            invalids.append(error)
    return valids, invalids


def write_error_sink(errors: Iterable[Mapping[str, Any]], sink_path: str) -> None:
    target = Path(sink_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        for error in errors:
            f.write(json.dumps(dict(error), default=str))
            f.write("\n")


def write_status(status: str, *, debug_mode: bool, last_batch_ts: str | None = None) -> None:
    if status not in {"RUNNING", "STOPPED", "ERROR"}:
        raise ValueError("status must be RUNNING, STOPPED, or ERROR")
    status_path = Path("status/spark_job_status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "last_heartbeat_ts": _utc_now_iso(),
        "last_batch_ts": last_batch_ts,
        "debug_mode": debug_mode,
    }
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_ingestion_sample(raw_order_records: Iterable[str], raw_courier_records: Iterable[str], *, debug_mode: bool = False) -> Dict[str, int]:
    cfg = load_ingestion_config()
    try:
        write_status("RUNNING", debug_mode=debug_mode)

        order_valid, order_invalid = split_valid_invalid_records(raw_order_records, "order_events")
        courier_valid, courier_invalid = split_valid_invalid_records(raw_courier_records, "courier_status")
        errors = order_invalid + courier_invalid
        if errors:
            write_error_sink(errors, cfg.error_sink_path)

        counts = {
            "order_valid_count": len(order_valid),
            "order_invalid_count": len(order_invalid),
            "courier_valid_count": len(courier_valid),
            "courier_invalid_count": len(courier_invalid),
        }
        log_info(_COMPONENT, "ingestion sample processed", {"counts": counts, "error_sink_path": cfg.error_sink_path})
        write_status("STOPPED", debug_mode=debug_mode, last_batch_ts=_utc_now_iso())
        return counts
    except Exception:
        write_status("ERROR", debug_mode=debug_mode)
        raise


def _error_record(reason_code: str, expected_feed_type: str, raw_payload: str, message: str) -> Dict[str, Any]:
    return {
        "timestamp": _utc_now_iso(),
        "component": _COMPONENT,
        "level": "ERROR",
        "message": message,
        "details": {
            "reason_code": reason_code,
            "expected_feed_type": expected_feed_type,
            "payload": raw_payload,
        },
    }


def _extract_namespace(conn_str: str) -> str:
    for part in conn_str.split(";"):
        part = part.strip()
        if part.lower().startswith("endpoint=sb://"):
            endpoint = part.split("=", 1)[1]
            host = endpoint.replace("sb://", "").strip("/")
            return host.split(".servicebus.windows.net")[0]
    raise ValueError("SPARK_EVENTHUB_CONNECTION_STRING must include Endpoint=sb://<namespace>.servicebus.windows.net/")

