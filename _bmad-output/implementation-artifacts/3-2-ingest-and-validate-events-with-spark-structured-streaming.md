# Story 3.2: Ingest and Validate Events with Spark Structured Streaming

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,  
I want Spark Structured Streaming jobs that ingest and validate events from Event Hubs,  
so that invalid records are routed to an error sink while the streaming job keeps running.

## Acceptance Criteria

1. Given the generator is publishing events to Event Hubs, when I start the ingestion Spark job with the documented configuration, then valid events are parsed into structured DataFrames using the expected schemas.
2. Given some events are malformed or schema-incompatible by design or by test data, when the ingestion job encounters them, then those events are written to an error sink (for example structured logs or a dedicated dataset) with a reason code, and the streaming job continues running without failing.

## Tasks / Subtasks

- [x] Task 1 (AC: #1): Define ingestion configuration and Spark source contract
  - [x] Add/confirm Spark Event Hubs source config in `config/spark_jobs.yaml` (or equivalent) for both feeds, including checkpoint and starting-offset behavior.
  - [x] Keep environment-driven secret handling (no secrets in repo); validate required connection settings fail fast with clear errors.
  - [x] Document feed-to-source mapping and expected input payload shape for order and courier streams.
- [x] Task 2 (AC: #1): Implement robust Event Hubs ingestion pipeline
  - [x] Implement/extend ingestion entrypoint in `stream_analytics/spark_jobs/ingestion.py` using Spark Structured Streaming.
  - [x] Parse payloads into typed DataFrames with schema enforcement for both feeds (snake_case columns preserved).
  - [x] Keep join keys and event-time fields (`order_id`, `courier_id`, `zone_id`, `event_time`) intact for downstream stories.
- [x] Task 3 (AC: #2): Implement validation and error sink path
  - [x] Add validation rules for malformed payloads, schema mismatches, and required-field failures.
  - [x] Route invalid records to an error sink with deterministic `reason_code` values and structured metadata.
  - [x] Ensure invalid-record handling is non-blocking so stream processing continues for valid records.
- [x] Task 4 (AC: #1, #2): Add observability and operational safety
  - [x] Emit structured logs (`timestamp`, `component`, `level`, `message`, `details`) for ingest success/failure counters.
  - [x] Update/emit status artifacts in `status/` using the standard lifecycle values (`RUNNING`, `STOPPED`, `ERROR`).
  - [x] Add troubleshooting notes for connectivity, auth, offset/checkpoint issues, and schema decode failures.
- [x] Task 5 (AC: #1, #2): Add tests and verification
  - [x] Add unit tests for schema parsing and validation/error classification logic.
  - [x] Add ingestion tests (with mocks/fixtures) covering mixed valid-invalid records and stream continuity behavior.
  - [x] Run test suite/lint checks and confirm no regressions in generator or existing ingestion-adjacent flows.

## Dev Notes

- Story and dependency context:
  - This is Epic 3, Story 2. It directly depends on stable publisher behavior from Story `3.1`.
  - Stories `3.3` to `3.5` rely on this story to provide clean, typed, and resilient streaming inputs.
- Existing repo intelligence:
  - `azure_sender.py` demonstrates Event Hub producer assumptions and currently uses environment variables (`EVENT_HUB_CONN_STR`, `EVENT_HUB_NAME`) that should stay secret-only.
  - `config/generator.yaml` already captures feed topic naming conventions and environment override style (`GENERATOR_*`), which should remain consistent with Spark-side config conventions.
- Mandatory architecture guardrails:
  - Keep snake_case for config keys, schema fields, DataFrame columns, and JSON/log payloads.
  - Place ingestion logic under `stream_analytics/spark_jobs/` and shared helpers under `stream_analytics/common/`.
  - Use consistent status artifact conventions: `status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`; values limited to `RUNNING`, `STOPPED`, `ERROR`.
- Validation and error-sink guidance:
  - Distinguish error classes with clear reason codes (for example `schema_mismatch`, `missing_field`, `invalid_timestamp`, `parse_error`).
  - Include enough error context for debugging while avoiding secret leakage or noisy payload dumping.
  - Preserve stream uptime: invalid events are isolated to sink/log path; valid events continue through pipeline.
- Performance and operations constraints:
  - Keep ingestion flow simple and deterministic for course demo operation and <15s end-to-end freshness target.
  - Preserve Windows/PowerShell compatibility for local orchestration and runbook commands.

### Project Structure Notes

- Preferred code placement:
  - Streaming ingestion and schema parsing: `stream_analytics/spark_jobs/`.
  - Shared config/logging/time helpers: `stream_analytics/common/`.
  - Tests mirrored under `tests/spark_jobs/` and related shared test modules.
- Keep dashboard read-only over curated outputs/status files; ingestion should not include UI concerns.
- Avoid introducing new root scripts for core ingestion logic; use thin wrappers only if backward compatibility requires them.

### Latest Tech Information

- `azure-eventhub` latest stable release identified: `5.15.1` (Nov 2025); keep Python Event Hub integration choices compatible with this baseline.
- Spark/Event Hubs ingestion guidance (2026): Spark commonly uses Event Hubs Kafka-compatible endpoint (`<namespace>.servicebus.windows.net:9093`) when legacy connector options are unavailable.
- Spark Structured Streaming best practice for resilience: enforce schema parsing with explicit invalid-record branches and checkpointed streaming queries for restart safety.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#story-3-2-ingest-and-validate-events-with-spark-structured-streaming`]
- [Source: `_bmad-output/planning-artifacts/prd.md#stream-processing--storage`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#api--communication-patterns`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#implementation-patterns--consistency-rules`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#project-structure--boundaries`]
- [Source: `_bmad-output/implementation-artifacts/3-1-publish-feeds-to-azure-event-hubs.md`]
- [Source: `config/generator.yaml`]
- [Source: `azure_sender.py`]
- [External Source: Azure SDK for Python Event Hubs docs/changelog]
- [External Source: Microsoft Learn + Databricks guidance for Spark Structured Streaming via Event Hubs Kafka endpoint]

## Dev Agent Record

### Agent Model Used

GPT-5.3 (Cursor create-story workflow)

### Debug Log References

- Add ingest-stage counters for total, valid, invalid, and reason-code distributions per feed.
- Capture startup/config and checkpoint context to speed troubleshooting and reproducibility.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Implemented Spark ingestion configuration contract with fail-fast env validation and Event Hubs Kafka source option builder.
- Added `stream_analytics.spark_jobs` ingestion module with validation routing, deterministic reason codes, structured error sink writes, and status artifact updates.
- Added Story 3.2 docs in `README.md` and `docs/design_note.md` for setup, mapping, and troubleshooting.
- Added Spark Structured Streaming ingestion entrypoint that reads Event Hubs via Kafka options and splits valid/invalid records into typed DataFrame branches.
- Added explicit ERROR status transitions for both sample and streaming ingestion paths.
- Added ingestion-focused tests and ran spark ingestion tests (`11 passed`).

### File List

- config/spark_jobs.yaml
- stream_analytics/__init__.py
- stream_analytics/spark_jobs/__init__.py
- stream_analytics/spark_jobs/config_models.py
- stream_analytics/spark_jobs/ingestion.py
- tests/spark_jobs/__init__.py
- tests/spark_jobs/test_ingestion_config_and_validation.py
- README.md
- docs/design_note.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Senior Developer Review (AI)

- Review date: 2026-04-14
- Reviewer: Javi (AI-assisted)
- Findings addressed:
  - Implemented Spark Structured Streaming ingestion path using Event Hubs Kafka source options.
  - Implemented typed schema parsing and deterministic valid/invalid stream branching for both feeds.
  - Implemented runtime ERROR lifecycle status updates on ingestion failures.
  - Added tests for source wiring and failure-state status behavior.
  - Synced story file list with actual changed files.
- Post-fix verification:
  - `pytest tests/spark_jobs/test_ingestion_config_and_validation.py` → `11 passed`.
- Outcome: Changes requested issues resolved; story ready for done status.

## Change Log

- 2026-04-14: Implemented Story 3.2 ingestion scaffolding (config contract, validation/error sink path, status artifacts, tests, and docs), and verified with full test pass.
- 2026-04-14: Addressed code review findings by adding Spark Structured Streaming ingestion wiring, typed DataFrame validation branches, explicit ERROR status handling, and expanded ingestion tests.
