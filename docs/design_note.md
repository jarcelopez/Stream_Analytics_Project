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
- `event_time` is encoded as an integer microsecond timestamp since epoch (matching the AVRO `timestamp-micros` logical type), which maps cleanly to Spark `timestamp` columns.
- Enum fields (`status`) are emitted as their uppercase string symbols.
- Nullable fields (`total_amount`, `delivery_time_seconds`, `active_order_id`) appear as either a concrete value or `null`.
- `feed_type` is always `"order_events"` or `"courier_status"` and is present in both AVRO and JSON representations to make routing explicit.

Tests in `tests/generator/test_serialization_and_two_feeds.py` assert:

- Both feeds are present in JSON and AVRO outputs.
- Required fields exist and are of basic expected types (for example `event_time` is an integer, IDs are strings).
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

Edge cases (late, duplicates, missing-step, impossible-duration, courier offline mid-flow) are intentionally not injected here; later stories add those behaviors on top of these schemas using dedicated configuration toggles. Because the baseline schemas and JSON formats already include the necessary keys and timestamps, edge-case events can be introduced without structural schema changes.

