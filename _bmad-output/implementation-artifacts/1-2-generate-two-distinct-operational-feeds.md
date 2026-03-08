# Story 1.2: Generate Two Distinct Operational Feeds

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,
I want to generate two distinct event streams (for example order events and courier status) in both JSON and AVRO formats,
so that downstream streaming jobs can rely on well‑defined inputs.

## Acceptance Criteria

1. **Two logical feeds produced from one generator (from `epics.md`, Story 1.2 & PRD FR1, FR3, FR11)**
   - **Given** valid generator configuration for entities,
   - **When** I run the generator in file or stream mode,
   - **Then** it produces an order‑events feed and a courier‑status feed as distinct logical streams (separate topics/paths and clearly distinguishable `feed_type` or equivalent identifiers).

2. **JSON outputs validate against documented schemas (from `epics.md` Story 1.2, PRD FR2, FR3, FR72–FR88)**
   - **Given** I configure the generator to output JSON,
   - **When** I run it,
   - **Then** it produces JSON events that validate against the documented order and courier schemas (field names, types, required/optional fields) and can be parsed by downstream Spark Structured Streaming jobs without schema errors.

3. **AVRO outputs validate against AVRO schemas and tooling (from `epics.md` Story 1.2, PRD FR2, FR3, FR72–FR88)**
   - **Given** I configure the generator to output AVRO,
   - **When** I run it,
   - **Then** it produces AVRO events that validate against the AVRO schemas for both feeds and can be decoded by standard AVRO tooling (CLI or Python libraries), with schema evolution handled in a documented, non‑breaking way.

4. **Configuration‑driven output formats and destinations (from PRD FR1–FR6, FR28–FR31; architecture “Config & Environment”)**
   - **Given** a configuration file (`config/generator.yaml`) and shared config loader,
   - **When** I specify output format (JSON, AVRO, or both) and destination (local files for Milestone 1, Event Hubs integration ready for Milestone 2),
   - **Then** the generator writes each logical feed to the configured outputs without hard‑coded paths, and defaults are suitable for development demos.

5. **Edge‑case‑safe base feeds (preparing for Stories 1.3, 1.4, 1.6; PRD FR5, FR32–FR35)**
   - **Given** edge‑case flags may later introduce late, duplicate, missing‑step, impossible‑duration, and courier‑offline behaviors,
   - **When** all edge‑case toggles are disabled,
   - **Then** the order and courier feeds produced by this story form a clean “baseline” stream that aligns with schemas and supports later edge‑case injection without structural changes.

6. **Documentation and discoverability (from PRD Documentation & Reflection FR36–FR39; `epics.md` documentation stories)**
   - **Given** a fresh user or grader,
   - **When** they read the README/design note sections related to the generator feeds,
   - **Then** they can clearly see which outputs correspond to the “order events” feed and which correspond to the “courier status” feed, and how to switch between JSON and AVRO modes using configuration only.

## Tasks / Subtasks

- [x] **T1 – Define and formalize feed contracts (schemas & semantics)** (AC 1–3, 5)
  - [x] T1.1 Extract and consolidate feed requirements from `epics.md` (Epic 1, Stories 1.1–1.3) and `prd.md` (FR1–FR6, FR32–FR33) into a concise internal design for the two feeds (Order Events and Courier Status), including:
        - entity keys (`order_id`, `restaurant_id`, `courier_id`, `zone_id`),
        - event‑time fields (`event_time`),
        - status / lifecycle fields (order states, courier availability),
        - basic metrics‑enabling fields (durations, amounts, flags).
  - [x] T1.2 Implement AVRO schemas under `stream_analytics/generator/schemas/` (e.g. `order_events.avsc`, `courier_status.avsc`), following architecture naming patterns (snake_case fields, explicit `event_time`, join IDs).
  - [x] T1.3 Define matching JSON representations (same field names and semantics) and document any differences (for example union types or enum encodings) in `docs/design_note.md`.

- [x] **T2 – Implement generator logic for two logical feeds** (AC 1–4)
  - [x] T2.1 Extend or implement generator core modules (e.g. `stream_analytics/generator/base_generators.py`, `entities.py`) to produce in‑memory events for the two feeds based exclusively on `GeneratorConfig` from Story 1.1 (no hard‑coded counts or rates).
  - [x] T2.2 Implement routing so that each generated event is clearly associated with its feed (`feed_type` or equivalent) and can be written to separate JSON/AVRO sinks or topics.
  - [x] T2.3 Implement write paths in `serialization.py` so that:
        - JSON events are written as line‑delimited JSON or small JSON batches per feed,
        - AVRO events are written using the AVRO schemas with proper schema registration and versioning hooks (even if registry is out of scope).

- [x] **T3 – Wire generator CLI and config to feeds and formats** (AC 2–4)
  - [x] T3.1 Extend `stream_analytics/generator/cli.py` to accept configuration for:
        - output formats (`output_formats: [json, avro]`),
        - destinations (local directories / file prefixes for Milestone 1),
        - optional placeholders for Event Hubs topic names to align with future Story 3.1.
  - [x] T3.2 Ensure CLI uses the shared `GeneratorConfig` (Story 1.1) and never duplicates config parsing logic.
  - [x] T3.3 Add a CLI “preview” or “sample” option that generates a small batch per feed to the configured outputs, to make it easy to validate schemas and event shapes in isolation.

- [x] **T4 – Validation, testing, and tooling integration** (AC 2–3, 5)
  - [x] T4.1 Add unit tests under `tests/generator/` to validate:
        - that JSON outputs conform to schemas (using Python validation or schema libraries),
        - that AVRO outputs can be round‑tripped through standard AVRO tooling.
  - [x] T4.2 Add at least one test that generates a small mixed batch and asserts that:
        - both feeds are present,
        - feed‑type separation is correct,
        - required fields are populated and well‑formed.
  - [x] T4.3 Integrate validation steps into local dev workflows (for example, `pytest` target or helper script) and document how to run them in README/design note.

- [ ] **T5 – Documentation and examples** (AC 4, 6)
  - [x] T5.1 Update `docs/design_note.md` with a section describing:
        - the two feeds and their purpose,
        - JSON vs AVRO formats,
        - how feed fields map to later analytics (metrics and anomaly detection).
  - [x] T5.2 Update README (or generator sub‑README) with:
        - how to run the generator to produce each format,
        - where files are written by default,
        - sample commands / config snippets for common demo scenarios.
  - [x] T5.3 Include at least one committed sample output (small JSON and AVRO batches) in a clearly labeled folder (for example `samples/`), or document how to generate samples on demand.

## Dev Notes

- **Requirements alignment**
  - This story directly realizes **Epic 1** (“Design and Run Synthetic Food‑Delivery Feeds”) and specifically **Story 1.2** from `epics.md`, while drawing on PRD functional requirements **FR1–FR6, FR32–FR33** and non‑functional requirements about demo realism and latency.
  - It depends on Story 1.1 for configuration scaffolding and prepares for Stories 1.3–1.6 by making sure that the baseline feeds are clean, schema‑driven, and easy to extend with edge cases, debug mode, and inspection tools.

- **Architecture and design guardrails** (from `architecture.md`)
  - Respect the established project structure:
    - Place generator code under `stream_analytics/generator/` (e.g. `base_generators.py`, `entities.py`, `serialization.py`).
    - Keep AVRO schemas in `stream_analytics/generator/schemas/`.
    - Use shared utilities in `stream_analytics/common/` for config loading, logging, and time handling.
  - Follow naming conventions:
    - Datasets and columns: **snake_case** (e.g. `order_events`, `courier_status`, `event_time`, `zone_id`, `delivery_time_seconds`).
    - Time window columns in downstream jobs: `window_start`, `window_end`.
  - Ensure generator outputs are designed to feed the **single denormalized metrics table** described in the architecture (`metrics_by_zone_restaurant_window`) by emitting stable identifiers and event‑time fields.

- **Operational expectations**
  - Default generator settings should be compatible with the PRD’s **NFR1** (≤ 15s end‑to‑end latency) and with “debug mode” expectations from Story 1.5, meaning:
    - manageable event rates for local runs,
    - small entity counts for quick “sample” runs,
    - clear documentation for scaling up volumes for richer demos.
  - Generator logs should follow the shared structured logging pattern:
    - `timestamp`, `component`, `level`, `message`, `details`, plus `feed_type` and `reason_code` where relevant.

### Project Structure Notes

- **Alignment with unified project structure**
  - Implement or extend:
    - `stream_analytics/generator/entities.py` for domain entities (zones, restaurants, couriers, orders) and realistic attribute distributions.
    - `stream_analytics/generator/base_generators.py` for order and courier feed generation logics.
    - `stream_analytics/generator/serialization.py` for JSON and AVRO writers that map generator objects to on‑disk representations.
    - `config/generator.yaml` to include output formats and paths, building on the Story 1.1 configuration.
  - Place tests in `tests/generator/` mirroring module layout (`test_base_generators.py`, `test_serialization.py`, `test_two_feeds_integration.py`).

- **Detected conflicts or variances (with rationale)**
  - If existing generator experiments or prototypes use different naming conventions (for example camelCase or mixed schemas), this story should:
    - converge them to the architecture‑defined snake_case schema,
    - provide a one‑time migration or alignment step documented in the design note.
  - Any temporary divergence from the proposed directory structure (for example while bootstrapping from the PySpark ETL cookiecutter) should be minimized and documented, with a plan to refactor into the unified `stream_analytics/` package.

### References

- **Epics & Stories**
  - `_bmad-output/planning-artifacts/epics.md` – Epic 1 overview and Story 1.2 definition (user story and acceptance criteria).
- **Product Requirements**
  - `_bmad-output/planning-artifacts/prd.md` – Functional Requirements FR1–FR6, FR32–FR33, plus sections on feeds, schemas, debug mode, and demo expectations.
- **Architecture**
  - `_bmad-output/planning-artifacts/architecture.md` – Architecture decisions around project structure, naming conventions, aggregated metrics model, and generator vs Spark vs dashboard boundaries.
- **Previous Story Intelligence**
  - `_bmad-output/implementation-artifacts/1-1-configure-core-feed-parameters.md` – Story 1.1 implementation details for `GeneratorConfig`, validation, and configuration patterns used by this story.

## Developer Context Section

This section distills everything a development agent needs to implement Story 1.2 without guessing or improvising architecture, tooling, or file layout.

- **Context from previous story (1.1)**
  - A `GeneratorConfig` model and configuration loader already exist, with configuration sourced from `config/generator.yaml` and environment overrides.
  - Generator entrypoints should already be wired to load `GeneratorConfig` before generating events; this story must reuse that mechanism, not introduce new config paths or ad‑hoc environment parsing.
  - Validation and structured logging patterns are in place; any new configuration or generator behavior introduced here must extend those patterns (same logging shape, same error‑handling philosophy).

- **Domain and analytics expectations**
  - Feeds must represent realistic food‑delivery operations:
    - Orders flow through a lifecycle (created, assigned, picked up, delivered, cancelled, etc.).
    - Couriers move across zones and have availability/online status and potentially location snapshots.
  - Edge cases (late, duplicates, missing steps, impossible durations, courier offline mid‑flow) will be layered on by later stories; this story focuses on “normal” but rich behavior.
  - Events must carry enough context to support:
    - **basic KPIs** (active orders, average delivery time, cancellation rate),
    - **intermediate metrics** (stateful/session‑based),
    - **advanced metrics** (Delivery Time Anomaly Score, Zone Stress Index).

- **Implementation boundaries**
  - **In scope for this story:**
    - Generator internals for producing and routing two feeds (Order Events, Courier Status).
    - AVRO/JSON serialization for those feeds.
    - Config surface for choosing formats and destinations.
    - Sample/demo generation and tests.
  - **Out of scope but must not be broken:**
    - Event Hubs integration (Story 3.1).
    - Spark Structured Streaming ingestion, windowing, metrics jobs (Epic 3).
    - Dashboard pages and orchestration logic (Epics 4 and 5).

## Technical Requirements

- **Inputs**
  - `GeneratorConfig` and shared config utilities from Story 1.1.
  - Entities and edge‑case requirements from PRD (`prd.md`) and epics (`epics.md`).

- **Outputs**
  - Two logical feeds:
    - `order_events` – order lifecycle and key timestamps, including fields like `order_id`, `restaurant_id`, `zone_id`, `event_time`, `status`, and any payload required for later metrics.
    - `courier_status` – courier positions and availability, including `courier_id`, `zone_id`, `event_time`, `status` (online/offline/assigned/idle), and metrics‑relevant attributes.
  - For Milestone 1 this likely means:
    - JSON: two separate files or directory trees (e.g. `data/order_events/json`, `data/courier_status/json`).
    - AVRO: separate AVRO outputs per feed (e.g. `data/order_events/avro`, `data/courier_status/avro`).

- **Performance, observability, and error handling**
  - Event generation should remain within volumes that support the NFR latency and debug expectations; generator throughput caps and entity counts should be controlled via configuration (supporting later debug mode).
  - Misconfigurations (invalid format list, invalid destination paths) should:
    - fail fast on startup,
    - produce structured error logs with `reason_code`,
    - never produce partial or ambiguous outputs.

## Architecture Compliance

- **Compliance with data and analytics architecture**
  - Feeds must be designed so that Spark ingestion can:
    - parse them into strongly typed DataFrames,
    - apply event‑time semantics and watermarks,
    - compute metrics into the unified `metrics_by_zone_restaurant_window` dataset.
  - Keys (`order_id`, `courier_id`, `zone_id`, `restaurant_id`) and `event_time` must be stable and consistent across generator, AVRO schemas, Spark schemas, Parquet outputs, and dashboard filters.

- **Compliance with project structure and boundaries**
  - Generator remains independent of dashboard implementation; it must not import Streamlit or dashboard code.
  - Any orchestration hooks (e.g. status files or debug flags) should be implemented via the `status/` artifacts and `common` utilities, not ad‑hoc new files.

## Library and Framework Requirements

- **Python and core stack**
  - Python ≥ 3.9 (aligned with Azure SDK and PySpark recommendations).

- **Azure Event Hubs libraries (for future streaming mode)**
  - Use the official `azure-eventhub` client, targeting a stable 5.x version (for example `azure-eventhub==5.15.0` as of mid‑2025) with Python 3.9+ support, per Azure SDK guidance.
  - Use the Azure Event Hubs Spark connector (via Maven coordinates) from the Spark side for streaming ingestion; do not attempt to pipe events directly from Python to Spark without Event Hubs.

- **PySpark Structured Streaming**
  - Ensure generator output formats and schemas are compatible with Spark reading patterns:
    - JSON: line‑delimited JSON with consistent schema.
    - AVRO: consistent AVRO schemas and schema evolution rules that Spark can handle without breaking jobs.

- **AVRO tooling**
  - Use the standard `avro` or `fastavro` Python libraries to:
    - validate events against AVRO schemas,
    - perform sample encodes/decodes in tests.

## File Structure Requirements

- Keep generator code and schemas under:
  - `stream_analytics/generator/` (core logic, CLI, edge cases).
  - `stream_analytics/generator/schemas/` (AVRO schema files).
  - `config/generator.yaml` (configuration for formats, destinations, rates, debug mode).
- Place generated sample outputs under a clearly named directory such as `samples/generator/` or `data/samples/`, keeping them out of the main curated Parquet outputs used by Spark.
- Follow the `status/` and `logs/` conventions from the architecture document if any status or debug indicators are written for generator runs.

## Testing Requirements

- **Unit tests**
  - Cover:
    - feed selection and routing logic,
    - JSON/AVRO serialization correctness (round‑trip through parsers),
    - schema validation helpers.
- **Integration / “smoke” tests**
  - At least one test that:
    - runs the generator in a small sample mode,
    - produces both feeds in both formats,
    - verifies file existence and basic schema correctness.
- **Future integration with Spark**
  - Optionally, add tests that:
    - load generated JSON/AVRO into a small local Spark session,
    - verify that the resulting DataFrame schema matches expectations from `spark_jobs/schemas.py`.

## Previous Story Intelligence

- Story 1.1 established:
  - A validated configuration model (`GeneratorConfig`) and CLI wiring, with structured error handling and tests.
  - A pattern for where generator code lives (`stream_analytics/generator/`) and how tests are organized (`tests/generator/`).
- This story must:
  - reuse the configuration and logging utilities rather than re‑inventing them,
  - treat any new configuration fields (e.g. output formats, destinations) as extensions to `GeneratorConfig`, with validation and documentation.

## Git Intelligence Summary

- Recent commits show that Story 1.1 implementation and initialization have already been committed (`implementation 1.1`, `partial 1.1 implementation`, `initialisation`), confirming:
  - the generator configuration scaffolding is in place,
  - project structure and conventions from the architecture document have started to be realized in code.
- When implementing this story, follow the existing patterns in generator and common modules rather than introducing new ad‑hoc structures.

## Latest Technical Information

- Use the current stable **Azure Event Hubs Python SDK (5.x)** and ensure compatibility with Python 3.9+; prefer the officially recommended versions from Azure SDK release notes when wiring streaming mode.
- For **PySpark Structured Streaming**, rely on the Azure Event Hubs Spark connector via Maven coordinates on the Spark side and design generator outputs to be “Spark‑friendly” (consistent schema, event‑time fields).
- For **Streamlit**, plan dashboards assuming a reasonably recent 1.x or 2.x version, and keep generator outputs and status artifacts straightforward to consume from the dashboard via the orchestrated pipeline.
- For **AVRO**, use well‑maintained Python libraries (e.g. `fastavro`) and avoid exotic schema patterns that are hard to map into Spark schemas or Python dataclasses.

## Project Context Reference

- This story is part of the **Stream_Analytics_Project**, a greenfield, Azure‑centric, streaming analytics education project targeting:
  - a Python‑first stack (generator, PySpark, Streamlit),
  - realistic but course‑feasible streaming demos,
  - alignment with PRD and architecture documents stored under `_bmad-output/planning-artifacts/`.

## Story Completion Status

- **Intended status after implementation:** `ready-for-dev` → `in-progress` (once a developer begins work) → `review` → `done`.
- **Sprint tracking alignment:**
  - `development_status["1-2-generate-two-distinct-operational-feeds"]` in `sprint-status.yaml` should be updated from `backlog` to `ready-for-dev` once this story context file is accepted.
- **Completion note template:**
  - “Ultimate context engine analysis completed – comprehensive developer guide for Story 1.2 created.”

## Dev Agent Record

### Agent Model Used

Cursor AI – GPT‑5.1 (`create-story` workflow)

### Debug Log References

- Reference generator configuration and CLI logs from Story 1.1 when implementing and validating this story.

### Completion Notes List

- “Defined and documented the two core feeds (order_events and courier_status) with JSON and AVRO contracts, aligned with PRD and architecture.”
- “Specified generator, configuration, and serialization changes needed to produce two distinct operational feeds suitable for Spark ingestion and downstream metrics.”
- “Captured technical guardrails around Azure Event Hubs, PySpark Structured Streaming, Streamlit, and AVRO usage to prevent outdated or incorrect implementations.”
 - “Implemented configuration-driven output formats and destinations for Story 1.2 sample feeds, plus JSON/AVRO validation tests and schema versioning hooks.”

### File List

- `_bmad-output/implementation-artifacts/1-2-generate-two-distinct-operational-feeds.md` – this story implementation document.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` – sprint tracking file (story status updated to `ready-for-dev` for this story).
- `_bmad-output/planning-artifacts/epics.md` – epics and BDD‑style story definitions.
- `_bmad-output/planning-artifacts/prd.md` – product requirements and NFRs.
- `_bmad-output/planning-artifacts/architecture.md` – architecture and conventions governing generator, Spark jobs, and dashboard.
 - `stream_analytics/generator/config_models.py` – generator configuration model extended with output formats, destinations, and Event Hubs placeholders.
 - `stream_analytics/generator/base_generators.py` – core sample generator for order_events and courier_status feeds, wired to configuration.
 - `stream_analytics/generator/entities.py` – in-memory domain entities and event factories for the two feeds.
 - `stream_analytics/generator/serialization.py` – JSON and AVRO writers, centralized hook for future registry/versioning behavior.
 - `stream_analytics/generator/schemas/order_events.avsc` – AVRO schema for the order_events feed (includes schema_version hook).
 - `stream_analytics/generator/schemas/courier_status.avsc` – AVRO schema for the courier_status feed (includes schema_version hook).
 - `stream_analytics/generator/cli.py` – generator CLI extended with Story 1.2 sample generation and config-driven destinations.
 - `tests/generator/test_serialization_and_two_feeds.py` – integration tests covering JSON/AVRO outputs and basic schema-aligned validation.

