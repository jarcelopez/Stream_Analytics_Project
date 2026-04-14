---
title: Stream Analytics Demo Project
description: Milestone 1 – Streaming data feed design and generation for a synthetic food-delivery platform
---

# Stream Analytics Demo Project

A real-time analytics pipeline for a synthetic food-delivery platform. This repository delivers two distinct event feeds, AVRO schemas, and a configurable Python generator that produces sample JSON and AVRO batches.

## Table of Contents

- [1.1 Create Two Feeds](#11-create-two-feeds)
- [1.2 Schema & Formats](#12-schema--formats)
- [1.3 Realism Requirements](#13-realism-requirements)
- [1.4 Deliverables](#14-deliverables)
- [Quick Start](#quick-start)
- [Running the Generator](#running-the-generator)
- [Further Reading](#further-reading)
- [License](#license)

---

## 1.1 Create Two Feeds

This project designs and implements two distinct streaming data feeds that represent the core operational dynamics of a real-time food-delivery platform:

1. **`order_events`** – Order lifecycle events (created, accepted, assigned, picked up, delivered, cancelled) with timestamps, amounts, and delivery metrics.
2. **`courier_status`** – Courier availability and position updates (online, offline, assigned, en route, idle) with optional active-order linkage.

### Why These Two Feeds Are Essential

- **Order events** capture the primary business flow: demand, fulfillment, and outcomes. They enable windowed KPIs (order volume, completion rate, cancellation rate), delivery-time analytics, and anomaly detection (impossible durations, missing lifecycle steps).
- **Courier status** captures supply-side dynamics: who is available, where they are, and whether they are actively delivering. Together with order events, it enables stream-table joins, zone-level stress metrics, and health views (e.g., offline couriers with active orders).

### What Analytics They Enable

- Windowed KPIs: order counts, average delivery time, cancellation rate per zone/restaurant/time window.
- Event-time processing: watermarks and late-data handling for out-of-order arrivals.
- Anomaly detection: impossible durations, missing steps, courier-offline mid-delivery scenarios.
- Zone Stress Index and similar metrics that combine both feeds.

### How Schemas Support Event-Time Processing and Late Data Handling

Both feeds include an `event_time` field (microsecond resolution) that maps to Spark `timestamp` columns. Join identifiers (`order_id`, `restaurant_id`, `courier_id`, `zone_id`) support stream-table joins and reference data patterns. The design note documents how edge cases (late events, duplicates, missing steps, impossible durations, courier offline) are encoded so downstream jobs can apply watermarks and event-time semantics correctly.

---

## 1.2 Schema & Formats

For each feed:

- **AVRO schema** – Defined in `stream_analytics/generator/schemas/` with sensible types, enums, optional fields, and a `schema_version` field for versioning.
- **Dual output** – Events are generated in both JSON and AVRO.
- **Event-time fields** – `event_time` (timestamp-micros) for analytics and watermarks.
- **Join identifiers** – `order_id`, `restaurant_id`, `courier_id`, `zone_id` for stream-table joins and reference data patterns.

| Feed           | Schema File           | Key Fields                                                                 |
|----------------|-----------------------|----------------------------------------------------------------------------|
| `order_events` | `order_events.avsc`    | `order_id`, `restaurant_id`, `courier_id`, `zone_id`, `event_time`, `status`, `total_amount`, `delivery_time_seconds` |
| `courier_status` | `courier_status.avsc` | `courier_id`, `zone_id`, `event_time`, `status`, `active_order_id`        |

---

## 1.3 Realism Requirements

The generator supports:

### Realistic Distributions

- Configurable demand levels (`low`, `medium`, `high`).
- Zone-level skew via configurable zone, restaurant, and courier counts.

### Configurability

- Number of zones, restaurants, and couriers.
- Events-per-second target.
- Demand level.
- Edge-case rates (see below).
- Output formats (JSON, AVRO, or both) and output directory.

### Edge Cases for Streaming Correctness

These are critical to demonstrate watermarks and event-time processing later:

| Edge Case              | Config Field              | Description                                                                 |
|------------------------|---------------------------|-----------------------------------------------------------------------------|
| Out-of-order (late)    | `late_event_rate`         | Events arrive with timestamps that appear “late” relative to processing order |
| Duplicates             | `duplicate_rate`          | Same logical event emitted more than once                                   |
| Missing steps          | `missing_step_rate`       | e.g., delivered without “picked up” in the lifecycle                         |
| Impossible durations   | `impossible_duration_rate`| Very large `delivery_time_seconds` for anomaly detection                   |
| Courier offline mid-delivery | `courier_offline_rate` | Courier goes OFFLINE while `active_order_id` is non-null                    |

---

## 1.4 Deliverables

This repository provides:

| Deliverable        | Location                                                                 |
|--------------------|---------------------------------------------------------------------------|
| Repository README  | This file: project overview, design rationale, run instructions         |
| Design note        | [docs/design_note.md](docs/design_note.md): fields, events, assumptions, planned analytics |
| Feed generator     | Python code in `stream_analytics/generator/`; config in `config/generator.yaml` |
| AVRO schemas       | `stream_analytics/generator/schemas/order_events.avsc`, `courier_status.avsc` |
| Sample data        | JSON and AVRO batches under `samples/generator/` (generated via CLI)      |

**Team structure:** Solo developer. Update this section if your project has multiple contributors.

---

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run tests:

```bash
pytest
```

4. Generate sample feeds:

```bash
python -m stream_analytics.generator.cli --sample
```

---

## Running the Generator

### Prerequisites

- Python 3.10 or newer
- Pip and a virtual environment (`venv` or `conda`)
- Git (to clone the repository)

### Environment Setup

From the project root:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Sample Mode (JSON + AVRO)

Produces small batches for both feeds:

```bash
python -m stream_analytics.generator.cli --sample
```

Outputs:

- `samples/generator/order_events/json/sample.jsonl`
- `samples/generator/order_events/avro/sample.avro`
- `samples/generator/courier_status/json/sample.jsonl`
- `samples/generator/courier_status/avro/sample.avro`


### Observing Edge Cases

1. Set non-zero edge-case rates in `config/generator.yaml`:

   ```yaml
   late_event_rate: 0.2
   duplicate_rate: 0.2
   missing_step_rate: 0.1
   impossible_duration_rate: 0.1
   courier_offline_rate: 0.1
   ```

2. Run the generator:

   ```bash
   python -m stream_analytics.generator.cli --sample --debug-sample --debug-seed 42 --output-dir samples/generator
   ```

3. Inspect the JSON/AVRO outputs under `samples/generator/` for late events, duplicates, missing steps, impossible durations, and courier-offline scenarios.

### Configuration

Core parameters live in `config/generator.yaml`. Override via environment variables (prefix `GENERATOR_`):

```bash
export GENERATOR_ZONE_COUNT=6
export GENERATOR_EVENTS_PER_SECOND=120
export GENERATOR_OUTPUT_BASE_DIR="data/samples"
export GENERATOR_OUTPUT_FORMATS='["json"]'
```

Print resolved configuration:

```bash
python -m stream_analytics.generator.cli --print-config
```

### Milestone 2: Stream to Azure Event Hubs

Use the publisher module to stream both feeds (`order_events` and `courier_status`) to Azure Event Hubs.

1. Set required credentials and optional hub overrides:

```powershell
$env:EVENTHUB_CONNECTION_STRING="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
$env:GENERATOR_EVENT_HUBS_ORDER_TOPIC="order-events"
$env:GENERATOR_EVENT_HUBS_COURIER_TOPIC="courier-status"
```

2. Send one batch per feed:

```bash
python -m stream_analytics.publisher.event_hub_publisher --batch
```

3. Stream continuously (Ctrl-C to stop):

```bash
python -m stream_analytics.publisher.event_hub_publisher --continuous
```

4. Run without Azure I/O to validate generation and logs:

```bash
python -m stream_analytics.publisher.event_hub_publisher --batch --dry-run
```

#### Partition/Key Strategy

- `order_events` uses `zone_id` as partition key to keep per-zone ordering and colocate zone analytics.
- `courier_status` uses `courier_id` as partition key to preserve courier timeline ordering.
- If a send fails, the publisher retries full batch sends up to three times before surfacing an error.

#### Event Hubs Troubleshooting

- **Auth failures (`Unauthorized`, CBS token errors):** check `EVENTHUB_CONNECTION_STRING` and ensure SAS policy has send rights.
- **Missing entity / wrong hub name:** verify `GENERATOR_EVENT_HUBS_ORDER_TOPIC` and `GENERATOR_EVENT_HUBS_COURIER_TOPIC` match existing Event Hubs.
- **Throughput / quota pressure:** reduce `sample_batch_size_per_feed` or `events_per_second`, or increase Event Hubs throughput units/processing units.

### Milestone 2: Spark Ingestion and Validation

Story 3.2 adds a Spark-ingestion contract that keeps stream processing alive while routing invalid records to an error sink.

1. Configure ingestion defaults in `config/spark_jobs.yaml`:

```yaml
order_event_hub_name: order-events
courier_event_hub_name: courier-status
consumer_group: $Default
starting_position: latest
checkpoint_base_dir: checkpoints/spark_jobs
error_sink_path: logs/spark_ingestion_errors.jsonl
```

2. Set required Event Hubs namespace connection string for Spark:

```powershell
$env:SPARK_EVENTHUB_CONNECTION_STRING="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
```

3. Optional overrides (same precedence style as generator config):

```powershell
$env:SPARK_JOBS_ORDER_EVENT_HUB_NAME="order-events"
$env:SPARK_JOBS_COURIER_EVENT_HUB_NAME="courier-status"
$env:SPARK_JOBS_STARTING_POSITION="earliest"
```

4. Validation behavior:
   - Valid records continue through ingestion.
   - Invalid records are written with reason codes such as `parse_error`, `schema_mismatch`, `missing_field`, `invalid_timestamp`, and `invalid_feed_type`.
   - Status is tracked in `status/spark_job_status.json` with `RUNNING`, `STOPPED`, or `ERROR`.

#### Spark Ingestion Troubleshooting

- **Missing `SPARK_EVENTHUB_CONNECTION_STRING`:** ingestion fails fast during config load.
- **Wrong Event Hub name:** check `order_event_hub_name` and `courier_event_hub_name` (or `SPARK_JOBS_*` overrides).
- **Unexpected replay/no replay:** verify `starting_position` (`latest` vs `earliest`) and checkpoint location.
- **No records in valid sink:** inspect `logs/spark_ingestion_errors.jsonl` for `reason_code` patterns and malformed payload evidence.

### Milestone 2: Event-Time Windows and Watermark Verification

Story 3.3 introduces explicit event-time semantics for stateful/windowed paths:

- `event_time` (microseconds) is converted to UTC Spark timestamp `event_time_ts`.
- Watermark/window defaults are configured in `config/spark_jobs.yaml`:
  - `watermark_delay`
  - `window_duration`
  - `window_slide`
  - `window_output_mode`
- Windowed memory sinks expose:
  - `order_events_windowed_kpis`
  - `courier_status_windowed_kpis`
- Curated window columns follow `window_start` and `window_end` naming.

#### How To Verify Watermark Behavior

1. Configure event-time window values (or env overrides):

```powershell
$env:SPARK_JOBS_WATERMARK_DELAY="10 minutes"
$env:SPARK_JOBS_WINDOW_DURATION="10 minutes"
$env:SPARK_JOBS_WINDOW_SLIDE="5 minutes"
```

2. Run Spark ingestion job and publish mixed on-time/late events from generator/publisher.
3. Inspect structured logs for watermark evidence (`windowing configuration initialized` and `window batch observability`).
4. Confirm that:
   - records within lateness threshold are represented in stateful updates,
   - records older than `max_event_time - watermark_delay` are treated as too-late for windowed aggregation paths.
5. Query memory tables and verify boundaries:

```sql
SELECT window_start, window_end, zone_id, feed_type, event_count
FROM order_events_windowed_kpis
ORDER BY window_start DESC;
```

### Milestone 2: Windowed KPI and Anomaly Metrics Dataset

Story 3.4 adds a curated denormalized Parquet dataset for dashboard-ready metrics:

- Dataset name/path: `metrics_by_zone_restaurant_window` at `data/metrics_by_zone_restaurant_window`
- Checkpoint isolation: `checkpoints/spark_jobs/metrics_by_zone_restaurant_window`
- Canonical dimensions:
  - `zone_id`
  - `restaurant_id`
  - `window_start`
  - `window_end`
- Core KPIs:
  - `active_orders`
  - `avg_delivery_time_seconds`
  - `cancellation_rate`
  - `total_orders`
- Intermediate/advanced metrics:
  - `orders_per_active_courier`
  - `zone_stress_index`
  - `delivery_time_ratio`
  - `stress_threshold`
  - `is_stressed`

#### How To Inspect Curated Metrics

1. Ensure Spark job config includes:

```yaml
metrics_sink_path: data/metrics_by_zone_restaurant_window
metrics_checkpoint_dir: checkpoints/spark_jobs/metrics_by_zone_restaurant_window
stress_index_threshold: 0.75
```

2. Run ingestion + streaming workload (publisher/generator as in previous milestone sections).
3. Inspect written Parquet:

```sql
SELECT
  zone_id,
  restaurant_id,
  window_start,
  window_end,
  total_orders,
  active_orders,
  avg_delivery_time_seconds,
  cancellation_rate,
  orders_per_active_courier,
  zone_stress_index,
  is_stressed
FROM parquet.`data/metrics_by_zone_restaurant_window`
ORDER BY window_start DESC, zone_id, restaurant_id;
```

---

## Further Reading

- [Design note](docs/design_note.md): Feed schemas, assumptions, edge-case encoding, and how the data enables downstream analytics
- [AVRO schemas](stream_analytics/generator/schemas/): `order_events.avsc` and `courier_status.avsc`

---

## License

See the repository for license terms.
