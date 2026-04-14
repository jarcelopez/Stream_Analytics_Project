# Stream Analytics Generator Design Note

This design note documents the configurable parameters and feed contracts for the synthetic generator and how they relate to the PRD’s functional requirements FR1–FR6 (and related documentation requirements).

## Core Configurable Parameters (Story 1.1)

The generator is configured via `config/generator.yaml` and a small set of environment-variable overrides (prefix `GENERATOR_`). Configuration is loaded through a shared helper (`stream_analytics/common/config.py`) into a strongly-typed `GeneratorConfig` model (`stream_analytics/generator/config_models.py`).

Key parameters:

- `zone_count` – number of delivery zones to simulate.
- `restaurant_count` – number of restaurants.
- `courier_count` – number of couriers.
- `demand_level` – qualitative demand setting, one of `low`, `medium`, `high`.
- `events_per_second` – target aggregate event rate for the generator.
- `debug_mode_max_events_per_second` – upper bound for debug mode throughput (used in FR32).
- `debug_mode_max_entity_count` – upper bound for entity counts in debug mode.
- `sample_batch_size_per_feed` – default batch size for sample outputs (used in FR6/FR33).

All fields use `snake_case` naming to stay consistent across generator code, Spark jobs, and dashboard logic.

### Mapping to Functional Requirements (FR1–FR6)

- **FR1 / FR4 – Configurable feeds and parameters**  
  The `GeneratorConfig` structure captures the primary knobs for feed configuration: entity counts and demand level. By centralising these in a single model and loading mechanism, later stories can wire generator logic and Spark jobs to the same configuration source. For Story 1.1 specifically, this implementation covers **configuration and validation only**; the actual event‑generation logic that consumes these values is introduced in later generator stories (for example Story 1.2 and beyond).

- **FR2 / FR3 – Schema-driven generation**  
  While AVRO schemas and dual JSON/AVRO outputs are introduced in later stories, `GeneratorConfig` provides the core dimensional parameters (zones, restaurants, couriers) that those schemas depend on.

- **FR5 – Edge-case control (future stories)**  
  Reserved fields such as `debug_mode_max_events_per_second`, `debug_mode_max_entity_count`, and `sample_batch_size_per_feed` are established here so that edge-case toggles and debug behaviors can be layered on without refactoring the configuration structure.

- **FR6 – Sample batches for inspection**  
  `sample_batch_size_per_feed` provides a default for small, inspectable batches, to be used when implementing sample-mode generation in later Milestone 1 stories.

### Notes on Acceptance Criteria Scope (Story 1.1)

Story 1.1 reuses acceptance criteria that describe end‑to‑end behavior (“the generator uses those values when producing events…”). Within this milestone, Story 1.1 is intentionally scoped to:

- Define and validate the configuration surface (`GeneratorConfig`, YAML, env overrides).
- Fail fast with clear, structured errors when configuration is invalid.

The behavioral aspects of AC1—verifying that emitted events and effective rates match the configured values within documented tolerances—are delivered when the actual generator logic is implemented in subsequent stories. Until then, AC1 should be interpreted as **partially satisfied** from a configuration perspective only.

### Validation and Error Handling

Validation rules on `GeneratorConfig` enforce:

- Non-negative, within-bounds counts for zones, restaurants, and couriers.
- Positive, bounded `events_per_second` targets suitable for course demos.
- Reasonable upper limits for debug/entity counts and sample batch sizes.

On validation failure, configuration loading fails fast and emits structured error logs using the shared logging helpers. Each error carries:

- `field` – the configuration field name.
- `reason` – human-readable explanation.
- `reason_code` – machine-readable code (for example `invalid_value`).

This pattern establishes the error-handling behavior that later generator and Spark stories will extend when dealing with invalid events and schemas.

## Two-Feed Contracts and Formats (Story 1.2)

Story 1.2 introduces concrete feed contracts and output formats for two logical feeds:

- `order_events` – order lifecycle and key timestamps (`order_id`, `restaurant_id`, `courier_id`, `zone_id`, `event_time`, `status`, `total_amount`, `delivery_time_seconds`, `feed_type`).
- `courier_status` – courier positions and availability (`courier_id`, `zone_id`, `event_time`, `status`, `active_order_id`, `feed_type`).

### AVRO Schemas

AVRO schemas are defined under `stream_analytics/generator/schemas/`:

- `order_events.avsc` – `OrderEvent` record with:
  - Keys: `order_id`, `restaurant_id`, `courier_id`, `zone_id`.
  - Event time: `event_time` as `timestamp-micros`.
  - Status: `status` as an `OrderStatus` enum (`CREATED`, `ACCEPTED`, `ASSIGNED`, `PICKED_UP`, `DELIVERED`, `CANCELLED`).
  - Metrics fields: nullable `total_amount`, `delivery_time_seconds`.
  - Versioning hook: `schema_version` (string, default `v1`).
  - Logical feed identifier: `feed_type` (always `order_events`).

- `courier_status.avsc` – `CourierStatusEvent` record with:
  - Keys: `courier_id`, `zone_id`.
  - Event time: `event_time` as `timestamp-micros`.
  - Status: `status` as a `CourierStatus` enum (`ONLINE`, `OFFLINE`, `ASSIGNED`, `EN_ROUTE_PICKUP`, `EN_ROUTE_DROPOFF`, `IDLE`).
  - Relationship field: nullable `active_order_id`.
  - Versioning hook: `schema_version` (string, default `v1`).
  - Logical feed identifier: `feed_type` (always `courier_status`).

These schemas are the contract between generator, Spark jobs, and downstream analytics. Future evolution should add fields in a backward-compatible way (using nullable fields and defaults) and bump `schema_version` accordingly.

### JSON Representations

JSON outputs are line-delimited JSON records that mirror the AVRO fields:

- Order feed JSON fields:
  - `order_id`, `restaurant_id`, `courier_id`, `zone_id`, `event_time`, `status`, `total_amount`, `delivery_time_seconds`, `feed_type`.
- Courier feed JSON fields:
  - `courier_id`, `zone_id`, `event_time`, `status`, `active_order_id`, `feed_type`.

Key conventions:

- All field names are `snake_case`.
- `event_time` is encoded in both AVRO and JSON as an integer microsecond timestamp since epoch (matching the AVRO `timestamp-micros` logical type). This keeps JSON samples, AVRO records, and schema validation aligned; Spark jobs then cast this long to a `timestamp` column on read, which is a small, intentional deviation from the architecture doc’s generic “ISO 8601 JSON” guidance.
- Enum fields (`status`) are emitted as their uppercase string symbols.
- Nullable fields (`total_amount`, `delivery_time_seconds`, `active_order_id`) appear as either a concrete value or `null`.
- `feed_type` is always `"order_events"` or `"courier_status"` and is present in both AVRO and JSON representations to make routing explicit.

Tests in `tests/generator/test_serialization_and_two_feeds.py` assert:

- Both feeds are present in JSON and AVRO outputs.
- Required fields exist and are of basic expected types (for example `event_time` is an integer microsecond timestamp and IDs are strings).
- `feed_type` separation between feeds is correct.

### Configuration-Driven Outputs

Story 1.2 extends `GeneratorConfig` with explicit output configuration:

- `output_base_dir` (string, default `samples/generator`) – base directory for generator outputs in file/sample modes.
- `output_formats` (list of `["json", "avro"]` values, default `["json", "avro"]`) – which formats to produce per feed.
- `event_hubs_order_topic` / `event_hubs_courier_topic` – optional placeholders for future Event Hubs topic names (used in Milestone 2).

In sample mode, the base generator (`generate_sample_feeds`) resolves paths under `output_base_dir` using the following layout:

- JSON:
  - `<output_base_dir>/order_events/json/sample.jsonl`
  - `<output_base_dir>/courier_status/json/sample.jsonl`
- AVRO:
  - `<output_base_dir>/order_events/avro/sample.avro`
  - `<output_base_dir>/courier_status/avro/sample.avro`

The function honours `output_formats`, so it can generate JSON only, AVRO only, or both for each feed. Invalid format lists are rejected at configuration-validation time via `GeneratorConfig.output_formats` validators.

These choices directly support:

- **FR2 / FR3** – dual JSON/AVRO outputs for both feeds, schema-aligned.
- **FR6** – small sample batches for inspection in a predictable, documented location.
- **FR28–FR31 (future)** – placeholders for Event Hubs topics so streaming-mode wiring can reuse the same configuration surface.

### Baseline vs Edge-Case Behavior

The Story 1.2 generator produces **baseline** (non edge-case) events:

- Order events cover the normal lifecycle: created, accepted, assigned, picked up, delivered, cancelled.
- Courier status events cover ONLINE/OFFLINE/ASSIGNED/EN_ROUTE_* and IDLE states, with optional `active_order_id`.

Story 1.3 extends this by adding **configuration-driven edge-case behavior** on top of the same schemas and JSON shapes:

- Configuration fields in `GeneratorConfig` and `config/generator.yaml`:
  - `late_event_rate`
  - `duplicate_rate`
  - `missing_step_rate`
  - `impossible_duration_rate`
  - `courier_offline_rate`
- All rates are probabilities in the [0.0, 1.0] range. A value of `0.0` means “effectively disabled”, providing the **edge-case off switch** required by FR5 / Story 1.3 AC1.

Edge-case encoding rules (JSON and AVRO):

- **Late / out-of-order events**  
  - Encoding: some `order_events` and `courier_status` records have their `event_time` shifted backwards by a fixed delay (for example 10 minutes), while all other fields remain schema-conformant.  
  - Purpose: downstream Spark jobs see these as late or out-of-order arrivals purely via `event_time`, matching PRD requirements for event-time semantics and watermarks.

- **Duplicates**  
  - Encoding: a subset of `order_events` records are duplicated **without changing** identifiers or status fields (same `order_id`, `restaurant_id`, `courier_id`, `zone_id`, `status`), so downstream systems see true logical duplicates.  
  - Purpose: duplicate handling can be implemented in Spark purely via keys and timestamps; no additional schema fields are required.

- **Missing steps**  
  - Encoding: a subset of `order_events` are dropped entirely from the stream, resulting in missing lifecycle statuses along an order’s timeline (for example a jump from `ACCEPTED` to `DELIVERED`).  
  - Purpose: Spark jobs and dashboard logic can detect/teach missing-step sequences solely via gaps in the status progression for a given `order_id`.

- **Impossible durations**  
  - Encoding: for some delivered orders (`status == "DELIVERED"` with non-null `delivery_time_seconds`), the generator inflates `delivery_time_seconds` to an unrealistic value (for example several hours) while keeping all other fields valid.  
  - Purpose: anomaly and SLA-breach logic can flag these cases using metrics over `delivery_time_seconds`, again without altering schemas.

- **Courier offline behavior**  
  - Encoding: a subset of `courier_status` records are forced to `status == "OFFLINE"`, sometimes even when `active_order_id` is non-null.  
  - Purpose: downstream jobs and dashboards can surface “courier offline with active orders” purely from existing `status` and `active_order_id` fields.

Because all of these behaviors are expressed using existing fields (`event_time`, `status`, `delivery_time_seconds`, `active_order_id`, IDs), **no AVRO schema evolution is required** for Story 1.3; JSON and AVRO remain structurally aligned.

For Story 1.6, these same encodings are documented and illustrated in more depth in:

- `docs/edge_cases.md` – shows concrete JSON examples, how to reproduce edge-case-heavy runs using `config/generator_edge_cases_demo.yaml`, and how each encoding is expected to surface in downstream Spark jobs and dashboard metrics (for example Delivery Time Anomaly Score and Zone Stress Index).

Sample outputs demonstrating each edge case are produced by the generator CLI:

- `python -m stream_analytics.generator.cli --sample --config-path config/generator.yaml`  
  - With all edge-case rates at `0.0`, produces a **baseline** sample batch per feed.  
  - With non-zero rates, emits **edge-case-rich** batches that exercise the encodings above.
- `python -m stream_analytics.generator.cli --sample --debug-sample --debug-seed 42 --config-path config/generator.yaml`  
  - Runs the same sample-mode generator in **debug mode**, clamping entity counts to `debug_mode_max_entity_count` and seeding the internal random generators.  
  - Re-running with the same configuration and `--debug-seed` value yields **reproducible debug batches** suitable for teaching/demo scenarios (within normal randomness guarantees and any future generator extensions).

Tests in `tests/generator/test_serialization_and_two_feeds.py` validate that:

- Baseline and edge-case configurations both produce schema-conformant JSON/AVRO outputs.
- Enabling edge-case rates changes the distributions as expected (for example more duplicates, more OFFLINE courier statuses, extremely large `delivery_time_seconds` values, and clearly late events due to widened `event_time` ranges), aligning with Story 1.3’s configurable-rate and encoding criteria.
- Additional focused tests exercise the edge-case helper directly to confirm that non-zero `late_event_rate` and `missing_step_rate` actually shift timestamps and drop some lifecycle events, respectively.
- Debug-style sample runs seeded via `seed_for_debug` are reproducible when the same configuration and seed are used, supporting Story 1.3’s deterministic debug-run requirement. Edge-case selection currently uses an internal fixed seed, making runs stable even though `--debug-seed` primarily controls the baseline synthetic data rather than the specific edge-case draws.

## Requirement and NFR Mapping (Story 2.1)

This section makes the requirement traceability from the PRD and architecture document explicit.

- **FR1–FR4 (configurable feeds, schemas, parameters):**  
  - Covered by **Core Configurable Parameters (Story 1.1)** and **Two-Feed Contracts and Formats (Story 1.2)**, where `GeneratorConfig`, AVRO schemas, and JSON shapes for `order_events` and `courier_status` are defined.
- **FR5 (edge-case control) and FR6 (sample batches):**  
  - Addressed in **Baseline vs Edge-Case Behavior** and **Edge-Case Examples by Feed**, plus the sample-mode CLI commands; edge-case rates and sample batch sizes are configuration-driven.
- **FR32–FR33 (debug mode, observability of edge cases):**  
  - Supported by debug-related configuration fields (`debug_mode_max_events_per_second`, `debug_mode_max_entity_count`, `sample_batch_size_per_feed`), the deterministic debug CLI (`--debug-sample`, `--debug-seed`), and structured logs in `logs/generator.log` that surface configuration errors and generator behavior.
- **Documentation FR36–FR37:**  
  - This design note, together with `docs/edge_cases.md`, forms the primary documentation of feed semantics and edge-case behavior referenced from the PRD and architecture doc.

Non-functional requirements (NFR1–NFR6) relate to the feeds and generator as follows:

- **NFR1–NFR2 (latency and responsiveness):**  
  - The design keeps schemas compact and uses configuration-driven sampling/output locations so that Streamlit and Spark can read small, time-windowed aggregates efficiently.
- **NFR3–NFR4 (synthetic, non-PII data and local access):**  
  - Feed schemas intentionally avoid PII-like fields; IDs (`order_id`, `courier_id`, `restaurant_id`, `zone_id`) are opaque, synthetic identifiers.
- **NFR5–NFR6 (setup time and robust demo runs):**  
  - Clear configuration, sample output locations, and documented edge cases are intended to make it possible to set up and run demos quickly, and to interpret failures via structured logs and sample outputs.

## Acceptance Criteria and Test Mapping (Story 2.1)

For quick review, this table maps the Story 2.1 acceptance criteria to sections of this design note and to the most relevant tests:

- **AC1 – Describe feeds, entities, event time, and analytics linkage:**  
  - Sections: **Two-Feed Contracts and Formats**, **Feed Roles in the Pipeline**, **How the Feeds Support Windows, Joins, and Anomaly Metrics**.  
  - Tests: `tests/generator/test_serialization_and_two_feeds.py` (feed presence and basic field/type checks).
- **AC2 – Document and encode edge cases:**  
  - Sections: **Baseline vs Edge-Case Behavior**, **Edge-Case Examples by Feed**.  
  - Tests: `tests/generator/test_serialization_and_two_feeds.py` and edge-case-focused tests under `tests/generator/` (where they exercise `late_event_rate`, `duplicate_rate`, `missing_step_rate`, `impossible_duration_rate`, `courier_offline_rate`).
- **AC3 – Trace FR1–FR6, FR32–FR33 to schema fields and behaviors:**  
  - Sections: **Mapping to Functional Requirements (FR1–FR6)**, **Baseline vs Edge-Case Behavior**, **Requirement and NFR Mapping (Story 2.1)**.
- **AC4 – Single source of truth for feed semantics:**  
  - Sections: all of the above, plus explicit references to AVRO schemas, configuration files, and sample output paths; together they are intended to be sufficient for Milestone 2 Spark and dashboard implementers without re-reading generator internals.

## Feed Roles in the Pipeline (Story 2.1)

This section ties the two feeds and their schemas directly to Milestone 2 analytics, Spark Structured Streaming jobs, and dashboard semantics.

### Order Events Feed (`order_events`)

The `order_events` feed is the primary source of truth for **order lifecycle, revenue, and delivery performance**:

- Keys: `order_id`, `restaurant_id`, `courier_id`, `zone_id`.
- Event time: `event_time` drives **event-time windows**, watermarks, and late-event handling.
- Lifecycle: `status` encodes the canonical sequence from `CREATED` → … → `DELIVERED` / `CANCELLED`.
- Metrics: `total_amount` and `delivery_time_seconds` back revenue and SLA/anomaly metrics.
- Routing: `feed_type == "order_events"` allows simple routing and feed separation.

Typical Milestone 2 windowed analytics that consume `order_events`:

- Per-zone and per-restaurant order volume per window (count by `zone_id`, `restaurant_id`).
- Revenue and average basket size per window (aggregations over `total_amount`).
- Delivery-time KPIs and anomaly scores using distributions of `delivery_time_seconds`.
- Order lifecycle health checks (e.g. fraction of orders that skip expected statuses).

### Courier Status Feed (`courier_status`)

The `courier_status` feed captures **courier availability and load**, which is critical for Zone Stress Index (ZSI) and similar operational metrics:

- Keys: `courier_id`, `zone_id`.
- Event time: `event_time` is aligned with `order_events` to enable windowed joins.
- Status: `status` distinguishes ONLINE/OFFLINE/ASSIGNED/EN_ROUTE_* and IDLE.
- Relationship: `active_order_id` links a courier to an order when they are busy.
- Routing: `feed_type == "courier_status"` separates this feed from `order_events`.

Milestone 2 analytics derived from `courier_status` include:

- Online/offline courier counts per zone and time window.
- Active load per zone (`count(distinct active_order_id)` where `status` is busy-like).
- Inputs to composite health scores such as **Zone Stress Index (ZSI)**, which typically combines:
  - Orders-in-progress per zone and window.
  - Number of ONLINE couriers in the same zone and window.
  - Historical baselines from previous windows.

### How the Feeds Support Windows, Joins, and Anomaly Metrics

- **Windows**  
  Both feeds share an `event_time` field (microsecond resolution) that maps cleanly to Spark `timestamp`. Milestone 2 jobs:
  - Define tumbling or sliding windows on `event_time`.
  - Apply watermarks to bound late data while still accepting the generator’s late events.

- **Joins**  
  Joins between feeds and with dimension tables primarily use:
  - `order_id` ↔ `active_order_id` (tie courier activity to specific orders).
  - `courier_id` and `zone_id` (join courier load to per-zone demand).
  - Time-based joins on windowed aggregates (e.g. windowed joins of order KPIs and courier capacity).

- **Anomaly and Health Metrics (incl. ZSI)**  
  - `delivery_time_seconds` powers long-tail and SLA-breach detection via windowed statistics.
  - `status` and `active_order_id` support detection of “courier offline with active orders”.
  - Aggregations over `order_id`, `courier_id`, and `zone_id` feed into ZSI-style scores that combine demand, capacity, and abnormal patterns (e.g. many late orders in zones with few ONLINE couriers).

## Edge-Case Examples by Feed (Story 2.1)

To make the edge-case encodings concrete within this design note (in addition to `docs/edge_cases.md`), this section shows one JSON-shaped example per edge case.

### Late / Out-of-Order Event (Order Events)

```json
{
  "order_id": "order-123",
  "restaurant_id": "rest-42",
  "courier_id": "courier-7",
  "zone_id": "zone-1",
  "event_time": 1700000000000000,
  "status": "DELIVERED",
  "total_amount": 32.5,
  "delivery_time_seconds": 1800.0,
  "schema_version": "v1",
  "feed_type": "order_events"
}
```

Interpretation: this record may arrive **after** newer events in the stream because the generator deliberately shifts `event_time` backwards for a fraction of orders (`late_event_rate`). Spark jobs treat this solely as a late event based on `event_time`, exercising watermarks and window semantics.

### Duplicate Event (Order Events)

```json
{
  "order_id": "order-456",
  "restaurant_id": "rest-10",
  "courier_id": "courier-2",
  "zone_id": "zone-3",
  "event_time": 1700000100000000,
  "status": "PICKED_UP",
  "total_amount": null,
  "delivery_time_seconds": null,
  "schema_version": "v1",
  "feed_type": "order_events"
}
```

When duplicated, the generator emits **the same record again** (identical IDs, `event_time`, and `status`). Downstream de-duplication relies on keys and timestamps; no extra schema fields are needed.

### Missing Step (Order Events)

```json
{
  "order_id": "order-789",
  "restaurant_id": "rest-5",
  "courier_id": "courier-9",
  "zone_id": "zone-2",
  "event_time": 1700000200000000,
  "status": "DELIVERED",
  "total_amount": 24.0,
  "delivery_time_seconds": 900.0,
  "schema_version": "v1",
  "feed_type": "order_events"
}
```

In a missing-step scenario, some intermediate statuses for this `order_id` (for example `ASSIGNED`, `PICKED_UP`) are never emitted due to `missing_step_rate`. Spark jobs detect these cases by analysing gaps in status sequences per order, without any schema changes.

### Impossible Duration (Order Events)

```json
{
  "order_id": "order-999",
  "restaurant_id": "rest-8",
  "courier_id": "courier-4",
  "zone_id": "zone-4",
  "event_time": 1700000300000000,
  "status": "DELIVERED",
  "total_amount": 18.0,
  "delivery_time_seconds": 21600.0,
  "schema_version": "v1",
  "feed_type": "order_events"
}
```

Here `delivery_time_seconds` is intentionally set to an unrealistic value (for example 6 hours) when `impossible_duration_rate` is non-zero. Anomaly metrics and ZSI-style health indicators consume these extreme values when computing per-zone and per-restaurant distributions.

### Courier Offline with Active Order (Courier Status)

```json
{
  "courier_id": "courier-4",
  "zone_id": "zone-4",
  "event_time": 1700000305000000,
  "status": "OFFLINE",
  "active_order_id": "order-999",
  "schema_version": "v1",
  "feed_type": "courier_status"
}
```

With `courier_offline_rate` > 0, the generator occasionally emits `status == "OFFLINE"` even when `active_order_id` is non-null. This feeds Milestone 2 health checks and dashboards that surface risky situations such as “offline courier with active orders” and contributes to ZSI and similar metrics.

Together, these examples demonstrate how **all required edge cases** (late, duplicate, missing-step, impossible-duration, courier-offline) are encoded using existing schema fields, enabling Milestone 2 Spark jobs and dashboards to demonstrate correct streaming semantics and anomaly handling without further schema changes.

## Event Hubs Publishing Strategy (Story 3.1)

Story 3.1 adds dual-feed streaming publication to Azure Event Hubs with deterministic partitioning for predictable analytics behavior.

### Feed Routing

- `order_events` feed publishes to the Event Hub resolved from:
  - `GENERATOR_EVENT_HUBS_ORDER_TOPIC` (env override), otherwise
  - `event_hubs_order_topic` in `config/generator.yaml`, otherwise
  - default `order-events`.
- `courier_status` feed publishes to the Event Hub resolved from:
  - `GENERATOR_EVENT_HUBS_COURIER_TOPIC` (env override), otherwise
  - `event_hubs_courier_topic` in `config/generator.yaml`, otherwise
  - default `courier-status`.
- Namespace credentials are loaded from `EVENTHUB_CONNECTION_STRING`; malformed or missing values fail fast with structured logs.

### Partition/Keying Rationale

- **Order feed partition key:** `zone_id`  
  This keeps events from the same zone together, which improves locality for zone-level windowed KPIs and joins.
- **Courier feed partition key:** `courier_id`  
  This preserves ordering for each courier timeline, useful for sequencing status transitions.
- **Trade-off:** deterministic keys improve per-entity ordering but can create hot partitions if one zone/courier dominates traffic. For course/demo throughput this is acceptable; production scaling would monitor partition skew and adapt keying.

### Reliability and Retry Behavior

- Publisher sends events in partition-key-specific batches.
- If a batch send fails with `EventHubError`, it retries the full batch up to three attempts with short backoff.
- Structured logs include feed/hub context, partition key, retry attempt, counts, and elapsed time to support troubleshooting and grading evidence.
