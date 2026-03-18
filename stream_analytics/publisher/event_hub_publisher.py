"""Publishes generated order_events and courier_status feeds to Azure Event Hubs.

Usage
-----
Batch mode (one shot – generate a batch, send, exit):
    python -m stream_analytics.publisher.event_hub_publisher --batch

Continuous mode (loops until Ctrl-C, respecting events_per_second from config):
    python -m stream_analytics.publisher.event_hub_publisher --continuous

Dry-run (generate events and log them to stdout without sending):
    python -m stream_analytics.publisher.event_hub_publisher --batch --dry-run

Required environment variable
------------------------------
    EVENTHUB_CONNECTION_STRING
        A Shared Access Signature (SAS) connection string for the Event Hubs
        namespace, e.g.:
          Endpoint=sb://<namespace>.servicebus.windows.net/;
          SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=<key>

Event Hub names
---------------
Set via YAML config or environment overrides (GENERATOR_ prefix):

    GENERATOR_EVENT_HUBS_ORDER_TOPIC    name of the hub for order_events
                                        (default: "order-events")
    GENERATOR_EVENT_HUBS_COURIER_TOPIC  name of the hub for courier_status
                                        (default: "courier-status")

Any other GeneratorConfig field can also be overridden with GENERATOR_*:
    GENERATOR_SAMPLE_BATCH_SIZE_PER_FEED=100
    GENERATOR_EVENTS_PER_SECOND=10
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Iterable, List, Mapping

from azure.eventhub import EventData, EventHubProducerClient, EventDataBatch
from azure.eventhub.exceptions import EventHubError

from stream_analytics.common.config import load_typed_config
from stream_analytics.common.logging_utils import log_info, log_error
from stream_analytics.generator.config_models import GeneratorConfig
from stream_analytics.generator.entities import generate_two_feeds_sample

_COMPONENT = "event_hub_publisher"
_CONFIG_PATH = "config/generator.yaml"

# Defaults used when the YAML / env vars leave the topic names unset.
_DEFAULT_ORDER_HUB = "order-events"
_DEFAULT_COURIER_HUB = "courier-status"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        log_error(
            _COMPONENT,
            f"Required environment variable '{name}' is not set.",
            {"hint": "Export the variable before running the publisher."},
        )
        sys.exit(1)
    return value


def _namespace_connection_string(conn_str: str) -> str:
    """Return a namespace-scoped connection string.

    Azure portal sometimes gives entity-scoped strings that include
    'EntityPath=<hub-name>'.  Passing such a string to
    EventHubProducerClient together with a *different* eventhub_name causes
    CBS token authentication to fail.  We strip EntityPath so that one
    connection string works for both hubs.
    """
    parts = [p for p in conn_str.split(";") if not p.lower().startswith("entitypath=")]
    cleaned = ";".join(parts)
    if cleaned != conn_str:
        log_info(
            _COMPONENT,
            "EntityPath stripped from connection string – using namespace-scoped credentials",
            {"hint": "Both hubs will authenticate with the namespace-level SAS key."},
        )
    return cleaned


def _send_feed(
    producer: EventHubProducerClient,
    events: Iterable[Mapping],
    hub_name: str,
    dry_run: bool,
) -> int:
    """Send all events in *events* to *producer*, batching automatically.

    Returns the total number of events sent (or would-be sent in dry-run).
    The SDK's EventDataBatch handles the 1 MB AMQP frame limit; when a batch
    fills up we flush it and open a new one.
    """
    total_sent = 0
    event_list: List[Mapping] = list(events)

    if dry_run:
        for event in event_list:
            log_info(_COMPONENT, "dry-run event", {"hub": hub_name, "event": event})
        return len(event_list)

    batch: EventDataBatch = producer.create_batch()
    for event in event_list:
        payload = EventData(json.dumps(event, default=str))
        # Use zone_id as the partition key so events from the same zone are
        # routed to the same partition, preserving per-zone ordering.
        try:
            batch.add(payload)
        except ValueError:
            # Current batch is full – flush and start a new one.
            producer.send_batch(batch)
            total_sent += len(batch)  # type: ignore[arg-type]
            batch = producer.create_batch()
            batch.add(payload)

    if len(batch) > 0:  # type: ignore[arg-type]
        producer.send_batch(batch)
        total_sent += len(batch)  # type: ignore[arg-type]

    return total_sent


def _validate_connection_string(conn_str: str) -> None:
    """Fail fast with a clear message if the connection string is malformed."""
    required_parts = ("Endpoint=sb://", "SharedAccessKeyName=", "SharedAccessKey=")
    missing = [p.split("=")[0] for p in required_parts if p.lower() not in conn_str.lower()]
    if missing:
        log_error(
            _COMPONENT,
            "EVENTHUB_CONNECTION_STRING appears malformed – missing required parts.",
            {
                "missing_parts": missing,
                "expected_format": (
                    "Endpoint=sb://<namespace>.servicebus.windows.net/;"
                    "SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
                ),
            },
        )
        sys.exit(1)


def _build_producer(connection_string: str, hub_name: str) -> EventHubProducerClient:
    return EventHubProducerClient.from_connection_string(
        conn_str=connection_string,
        eventhub_name=hub_name,
    )


# ---------------------------------------------------------------------------
# Core publish logic
# ---------------------------------------------------------------------------

def publish_once(
    cfg: GeneratorConfig,
    connection_string: str,
    order_hub: str,
    courier_hub: str,
    dry_run: bool,
) -> dict:
    """Generate one batch from each feed and publish to Event Hubs.

    Returns a dict with send statistics for logging/testing.
    """
    order_events, courier_events = generate_two_feeds_sample(
        zone_count=cfg.zone_count,
        restaurant_count=cfg.restaurant_count,
        courier_count=cfg.courier_count,
        sample_batch_size_per_feed=cfg.sample_batch_size_per_feed or 500,
    )

    stats: dict = {"orders_sent": 0, "couriers_sent": 0, "errors": []}

    for hub_name, events, stat_key in [
        (order_hub, order_events, "orders_sent"),
        (courier_hub, courier_events, "couriers_sent"),
    ]:
        if dry_run:
            count = _send_feed(None, events, hub_name, dry_run=True)  # type: ignore[arg-type]
            stats[stat_key] = count
            continue

        producer = _build_producer(connection_string, hub_name)
        try:
            with producer:
                count = _send_feed(producer, events, hub_name, dry_run=False)
                stats[stat_key] = count
        except EventHubError as exc:
            msg = f"EventHubError while sending to '{hub_name}': {exc}"
            log_error(_COMPONENT, msg, {"hub": hub_name})
            stats["errors"].append(msg)

    return stats


def run_batch(cfg: GeneratorConfig, connection_string: str, order_hub: str, courier_hub: str, dry_run: bool) -> None:
    log_info(_COMPONENT, "batch run starting", {
        "order_hub": order_hub,
        "courier_hub": courier_hub,
        "batch_size_per_feed": cfg.sample_batch_size_per_feed,
        "dry_run": dry_run,
    })
    t0 = time.monotonic()
    stats = publish_once(cfg, connection_string, order_hub, courier_hub, dry_run)
    elapsed = time.monotonic() - t0
    log_info(_COMPONENT, "batch run complete", {**stats, "elapsed_s": round(elapsed, 3)})


def run_continuous(
    cfg: GeneratorConfig,
    connection_string: str,
    order_hub: str,
    courier_hub: str,
    dry_run: bool,
) -> None:
    batch_size = cfg.sample_batch_size_per_feed or 500
    eps = cfg.events_per_second
    # Two feeds, so total events per iteration = 2 * batch_size.
    sleep_s = (2 * batch_size) / eps

    log_info(_COMPONENT, "continuous streaming started", {
        "order_hub": order_hub,
        "courier_hub": courier_hub,
        "batch_size_per_feed": batch_size,
        "events_per_second_target": eps,
        "sleep_between_batches_s": round(sleep_s, 3),
        "dry_run": dry_run,
    })

    iteration = 0
    try:
        while True:
            iteration += 1
            t0 = time.monotonic()
            stats = publish_once(cfg, connection_string, order_hub, courier_hub, dry_run)
            elapsed = time.monotonic() - t0

            log_info(_COMPONENT, "iteration complete", {
                "iteration": iteration,
                **stats,
                "elapsed_s": round(elapsed, 3),
            })

            if stats["errors"]:
                log_error(_COMPONENT, "errors occurred – pausing before retry", {
                    "errors": stats["errors"],
                })

            remaining = sleep_s - elapsed
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        log_info(_COMPONENT, "continuous streaming stopped by user", {"iterations": iteration})


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish synthetic food-delivery events to Azure Event Hubs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--batch",
        action="store_true",
        help="Generate one batch per feed, publish, and exit.",
    )
    mode.add_argument(
        "--continuous",
        action="store_true",
        help="Loop indefinitely, publishing batches at the configured events_per_second rate.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Log events to stdout instead of sending to Event Hubs (no connection required).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    cfg: GeneratorConfig = load_typed_config(
        relative_yaml_path=_CONFIG_PATH,
        model_type=GeneratorConfig,
        env_prefix="GENERATOR",
    )

    order_hub = cfg.event_hubs_order_topic or _DEFAULT_ORDER_HUB
    courier_hub = cfg.event_hubs_courier_topic or _DEFAULT_COURIER_HUB

    connection_string = ""
    if not args.dry_run:
        connection_string = _namespace_connection_string(
            _require_env("EVENTHUB_CONNECTION_STRING")
        )
        _validate_connection_string(connection_string)

    if args.batch:
        run_batch(cfg, connection_string, order_hub, courier_hub, dry_run=args.dry_run)
    else:
        run_continuous(cfg, connection_string, order_hub, courier_hub, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
