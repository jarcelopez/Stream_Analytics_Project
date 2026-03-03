# Edge-Case Encodings and Downstream Interpretation

This document explains how the generator encodes key edge cases in the `order_events` and `courier_status` feeds, how to reproduce those behaviors using the generator configuration, and how they are expected to appear in downstream Spark Structured Streaming jobs and dashboard metrics.

It is intended as the primary reference for Story 1.6 and connects directly to FR32–FR35 and the streaming correctness requirements in the PRD.

## Curated Example Files

For quick inspection, this project includes small curated JSONL slices that show each edge case in isolation:

- Order events: `samples/generator/order_events/json/edge_cases/order_events_edge_cases.jsonl`
- Courier status: `samples/generator/courier_status/json/edge_cases/courier_status_edge_cases.jsonl`

All records in these files conform to the AVRO schemas in `stream_analytics/generator/schemas/order_events.avsc` and `stream_analytics/generator/schemas/courier_status.avsc`, as enforced by:

- `tests/generator/test_edge_case_example_files_validate_against_schemas.py`

The curated slices are intentionally small and human-readable; they complement, rather than replace, the larger sample/debug batches produced by the generator CLI.

## How to Reproduce Edge-Case-Rich Runs

The generator can produce both baseline and edge-case-rich batches using configuration only (no code changes).

### Baseline debug/sample run (no edge cases)

From the project root:

```bash
python -m stream_analytics.generator.cli \
  --config-path config/generator.yaml \
  --sample \
  --debug-sample \
  --debug-seed 42 \
  --output-dir samples/generator/debug_baseline
```

With all edge-case rates set to `0.0` in `config/generator.yaml`, this produces:

- `samples/generator/debug_baseline/order_events/json/sample.jsonl`
- `samples/generator/debug_baseline/courier_status/json/sample.jsonl`

These batches contain only baseline behavior (no deliberate late events, duplicates, missing steps, impossible durations, or forced courier-offline patterns).

### Edge-case demo run (rich mix of behaviors)

For a focused edge-case demo, use the Story 1.6 config:

```bash
python -m stream_analytics.generator.cli \
  --config-path config/generator_edge_cases_demo.yaml \
  --sample \
  --debug-sample \
  --debug-seed 7 \
  --output-dir samples/generator/edge_case_demo
```

This configuration:

- Keeps entity counts and batch sizes small enough for quick inspection.
- Sets non-zero rates for:
  - `late_event_rate`
  - `duplicate_rate`
  - `missing_step_rate`
  - `impossible_duration_rate`
  - `courier_offline_rate`
- Produces JSON (and AVRO) samples under:
  - `samples/generator/edge_case_demo/order_events/json/sample.jsonl`
  - `samples/generator/edge_case_demo/courier_status/json/sample.jsonl`

These edge-case-rich batches can be compared directly against the curated slices in `samples/generator/*/json/edge_cases/` to see the same patterns at larger scale.

## Edge-Case Encodings in the Feeds

This section describes, for each edge case, how it is encoded in the data model and which fields are most important for downstream logic.

### 1. Late and Out-of-Order Events

**Encoding (order_events and courier_status):**

- Fields used:
  - `event_time` (microsecond timestamp)
  - `status`
  - IDs: `order_id`, `courier_id`, `zone_id`
- Some events have their `event_time` shifted **backwards** relative to the natural timeline of events for the same entity.
  - Example patterns in order events:
    - A `PICKED_UP` event whose `event_time` is earlier than the corresponding `CREATED` or `ACCEPTED` events.
    - A `DELIVERED` event arriving with an `event_time` that falls well before recent baseline events in the same zone.
  - Similar shifts can occur in `courier_status` (for example toggling ONLINE/OFFLINE or ASSIGNED states with back-dated `event_time`).

**Downstream interpretation:**

- **Spark Structured Streaming:**
  - Event-time semantics are driven by `event_time` and `withWatermark("event_time", "<delay>")` in windowed queries.
  - Late events that fall **within** the watermark horizon are still aggregated but may update previously emitted windows (depending on output mode).
  - Events later than the watermark horizon are dropped from state, which is exactly what the PRD expects for long-delayed events.
- **Metrics and dashboards:**
  - Windowed KPIs (for example on-time delivery rate by `zone_id` and time window) will see late events either:
    - Counted but potentially flagged as late within the window, or
    - Discarded after the watermark, contributing to discrepancies between raw event counts and business KPIs.

When testing, you can:

- Group by `window(event_time, "<size>")` and `zone_id` to see which windows receive late arrivals.
- Compare counts with and without a strict watermark to understand how aggressively late events are dropped.

### 2. Duplicates

**Encoding (order_events):**

- Fields used:
  - All order event fields, especially:
    - `order_id`, `restaurant_id`, `courier_id`, `zone_id`
    - `event_time`
    - `status`
- A subset of `order_events` records are **duplicated without modification**:
  - Same `order_id`, same `event_time`, same `status`, same amounts.
  - The curated examples show identical JSON objects repeated in the stream.

**Downstream interpretation:**

- **Spark Structured Streaming:**
  - Duplicates can cause over-counting in aggregations such as:
    - Total orders per zone and window.
    - Sum of `total_amount` per restaurant.
  - De-duplication strategies typically:
    - Use a primary key (`order_id`, `event_time`) or a full-record hash in a stateful map.
    - Drop subsequent duplicates within a configured retention period.
- **Metrics and dashboards:**
  - Without de-duplication, duplicates inflate:
    - Order volume metrics.
    - Revenue and average ticket size.
  - The PRD’s anomaly metrics can treat unexpected spikes as potential data quality issues; curated duplicates provide concrete cases to validate those alerts.

### 3. Missing-Step Sequences

**Encoding (order_events):**

- Fields used:
  - `order_id`, `status`, `event_time`
- For some `order_id`s, intermediate lifecycle statuses are omitted entirely:
  - Example: `CREATED` → `DELIVERED` with no `ACCEPTED` or `PICKED_UP` events.
  - Example: `ACCEPTED` → `CANCELLED` with no explicit `ASSIGNED`.

**Downstream interpretation:**

- **Spark Structured Streaming:**
  - State machines keyed by `order_id` will see incomplete transitions and should:
    - Either tolerate and classify them as “incomplete lifecycle”.
    - Or raise flags for missing expected statuses.
- **Metrics and dashboards:**
  - Missing steps directly affect:
    - Funnel-style metrics (conversion from CREATED → ACCEPTED → DELIVERED).
    - Derived KPIs like “average time from ACCEPTED to PICKED_UP”, which are undefined when one step is missing.
  - Curated examples allow tests to assert that:
    - Missing steps are either excluded or clearly labelled in KPI outputs.

### 4. Impossible Durations

**Encoding (order_events):**

- Fields used:
  - `status`
  - `delivery_time_seconds`
  - `event_time`
  - `order_id`, `zone_id`
- For some `DELIVERED` orders:
  - `delivery_time_seconds` is set to a **very large** value (for example > 4 hours).
  - The corresponding lifecycle timestamps remain schema-valid, so the anomaly is encoded purely in the duration field.

**Downstream interpretation:**

- **Spark Structured Streaming:**
  - Windowed aggregations can compute:
    - Average and percentile delivery times by `zone_id` and time window.
    - Counts of orders with `delivery_time_seconds` above SLA thresholds.
  - With watermarks applied, these anomalous durations still participate in windows as long as the events are within the watermark horizon.
- **Metrics and dashboards:**
  - **Delivery Time Anomaly Score** should:
    - Assign high anomaly scores to these extreme durations.
    - Surface them in outlier tables/plots for investigation.
  - Curated impossible-duration examples can be used in tests to assert that:
    - Z-score or percentile-based anomaly logic actually highlights them.
    - Aggregated SLAs (for example P95 delivery time) react as expected.

### 5. Courier Offline Scenarios

**Encoding (courier_status):**

- Fields used:
  - `courier_id`, `zone_id`
  - `status`
  - `active_order_id`
  - `event_time`
- Example patterns:
  - Sequences where a courier toggles `ONLINE → OFFLINE → ONLINE` in a short time window.
  - More subtle edge case: `status == "OFFLINE"` while `active_order_id` remains non-null, indicating a courier is marked offline despite having an active order.

**Downstream interpretation:**

- **Spark Structured Streaming:**
  - Zone-level load and availability calculations (for example Zone Stress Index) depend on:
    - Number of ONLINE vs OFFLINE couriers per zone, per window.
    - Number of ACTIVE orders per courier.
  - OFFLINE events with active orders should be treated as:
    - High-risk conditions for SLA breaches.
    - Potential triggers for re-assignment or escalation logic in more advanced pipelines.
- **Metrics and dashboards:**
  - Zone Stress Index and related health views can:
    - Increase stress when many couriers are OFFLINE while orders remain active.
    - Highlight zones where offline-with-active-order scenarios occur unusually often (possible generator misconfiguration or operational issue).

## How This Connects to the PRD and Architecture

- **PRD (FR32–FR35)** describes:
  - The need to **inspect example events and schemas** to understand edge-case encodings.
  - The requirement that downstream metrics (delivery-time anomalies, Zone Stress Index) behave correctly in the presence of late, duplicate, missing-step, impossible-duration, and offline scenarios.
- **Architecture document**:
  - Defines `order_events` and `courier_status` as foundational feeds.
  - Describes how watermarks, windows, and anomaly metrics are configured in Spark jobs.

This document plus the curated examples and demo configurations together provide the concrete contract that downstream Spark jobs and dashboards should honour. Any future changes to edge-case encodings or schemas should update:

- The AVRO schemas in `stream_analytics/generator/schemas/`.
- The curated example files under `samples/generator/*/json/edge_cases/`.
- This document, including notes on how metrics and dashboards are expected to react.


