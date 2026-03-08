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

---

## Further Reading

- [Design note](docs/design_note.md): Feed schemas, assumptions, edge-case encoding, and how the data enables downstream analytics
- [AVRO schemas](stream_analytics/generator/schemas/): `order_events.avsc` and `courier_status.avsc`

---

## License

See the repository for license terms.
