# Story 3.3: Configure Event-Time Semantics, Watermarks, and Windows

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,  
I want to configure event-time semantics, watermarks, and windowing in the Spark jobs,  
so that metrics properly handle late and out-of-order events.

## Acceptance Criteria

1. Given the ingestion and transformation jobs are running, when I inspect the Spark job definitions, then they use an event-time column and watermarks consistent with the PRD and documented edge-case behavior.
2. Given I run the pipeline with a mix of on-time and deliberately late/out-of-order events, when I review the resulting metrics and/or logs, then late events are handled according to the configured watermarks (for example included within allowed lateness and ignored beyond it) and this behavior is observable and explainable.

## Tasks / Subtasks

- [x] Task 1 (AC: #1): Establish canonical event-time column handling from ingestion outputs
  - [x] Confirm typed streaming payloads in `stream_analytics/spark_jobs/ingestion.py` are converted from microsecond epoch `event_time` (long) to Spark `timestamp` column (for example `event_time_ts`) before stateful operations.
  - [x] Keep `event_time` (raw numeric) available when useful for debugging, but ensure watermarks/windows use the timestamp-typed column only.
  - [x] Validate timezone assumption (UTC) and document conversion logic to prevent silent skew in window boundaries.
- [x] Task 2 (AC: #1): Add watermark and window configuration contract
  - [x] Add or extend config values in `config/spark_jobs.yaml` for watermark delay and window strategy (duration and slide, if applicable).
  - [x] Keep env override behavior through the existing typed config loader (`SPARK_JOBS_` prefix); avoid introducing new ad-hoc config parsing.
  - [x] Fail fast with clear errors for invalid duration strings or impossible settings (for example watermark <= 0, slide > window if policy disallows it).
- [x] Task 3 (AC: #1, #2): Implement windowed aggregation foundations in Spark jobs
  - [x] Build/extend Spark job module(s) under `stream_analytics/spark_jobs/` to apply `.withWatermark(...)` before windowed/grouped stateful operations.
  - [x] Use `window_start` and `window_end` output naming conventions in curated results to stay compatible with downstream stories (`3.4`, `3.5`) and dashboard filters.
  - [x] Ensure implementation semantics are explicit: late events inside threshold update aggregates; events beyond watermark threshold are dropped from stateful aggregation paths.
- [x] Task 4 (AC: #2): Make late-data behavior observable and explainable
  - [x] Add structured logs and/or counters indicating watermark/window config and per-batch evidence of late-data handling (accepted-late vs too-late dropped where measurable).
  - [x] Record debugging-friendly metadata in logs/status (for example current batch watermark, trigger timestamp, and batch output counts when available).
  - [x] Update runbook notes (`README.md` and/or `docs/design_note.md`) with a short "how to verify watermark behavior" procedure.
- [x] Task 5 (AC: #1, #2): Add tests for deterministic correctness
  - [x] Add tests under `tests/spark_jobs/` covering event-time conversion correctness and config validation.
  - [x] Add behavior tests that simulate on-time and late records and verify inclusion/exclusion semantics around the configured watermark boundary.
  - [x] Verify Story `3.2` ingestion behavior remains stable (no regressions in valid/invalid routing and status artifact lifecycle).

## Dev Notes

- Story and dependency context:
  - This is Epic 3, Story 3. It depends directly on Story `3.2` outputs (`order_events_valid`, `courier_status_valid`, error sink and status conventions).
  - This story is the correctness backbone for Story `3.4` KPI/stateful/anomaly computations and Story `3.5` curated Parquet semantics.
- Existing implementation intelligence from Story 3.2:
  - `stream_analytics/spark_jobs/ingestion.py` validates `event_time` as integer micros and produces typed valid/invalid branches.
  - Event Hubs ingestion path is already configured through `config/spark_jobs.yaml` and `SparkIngestionConfig`; reuse this model for watermark/window configuration instead of creating separate config mechanisms.
  - Current ingestion queries are memory/error-sink oriented; this story should introduce the first event-time stateful layer while preserving current ingestion reliability and error handling.
- Architecture guardrails that MUST be followed:
  - Keep snake_case naming for datasets, columns, config keys, and logs.
  - Keep Spark modules under `stream_analytics/spark_jobs/` and shared helpers under `stream_analytics/common/`.
  - Standard time-window column names must be `window_start` and `window_end`.
  - Preserve status artifact shape and semantics (`status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`) and values (`RUNNING`, `STOPPED`, `ERROR`).
- Watermark and output mode guardrails:
  - Use watermark on the same event-time column used in aggregation/window operations.
  - If using append mode for windowed aggregates, expect delayed outputs until watermark passes window end; if near-real-time partial visibility is required, justify/update output mode accordingly.
  - Avoid unbounded state: no stateful aggregation without explicit watermarking policy.
- Anti-reinvention guidance:
  - Reuse existing config loader, logging helpers, and status conventions.
  - Do not create parallel one-off scripts for watermark demos; keep logic in package modules and tests.
- Risks and pitfalls to explicitly prevent:
  - Incorrect epoch conversion (micros vs millis/seconds) leading to wrong watermark progression.
  - Applying watermark after aggregation, which breaks intended semantics.
  - Window/output mode mismatches causing silent latency surprises or sink incompatibility.
  - Inconsistent event-time field naming between order and courier paths causing join/window drift in Story `3.4`.

### Project Structure Notes

- Preferred code placement:
  - Event-time conversion and reusable transformations: `stream_analytics/spark_jobs/` (or shared helper in `stream_analytics/common/time_utils.py` if reused broadly).
  - Config model updates: `stream_analytics/spark_jobs/config_models.py` plus `config/spark_jobs.yaml`.
  - Tests: `tests/spark_jobs/` with focused unit/integration-style Spark logic tests.
- Keep dashboard code out of this story's implementation scope; this is streaming correctness groundwork for downstream analytics and UI stories.

### Previous Story Intelligence

- Story `3.2` established a reliable ingest/validate split with deterministic reason codes and status artifact lifecycle handling; preserve those contracts unchanged while layering event-time semantics on top.
- Story `3.2` already aligned Spark-side ingestion with Event Hubs Kafka-compatible options and checkpoint paths; reuse these patterns for any new stateful query checkpointing.
- Avoid introducing secret/config drift: follow the existing env-driven config approach (`SPARK_EVENTHUB_CONNECTION_STRING` and `SPARK_JOBS_*` overrides).

### Git Intelligence Summary

- Recent commits: `story 3.2`, `story 3.1`, and milestone commits show a short, pragmatic commit style and incremental delivery by story.
- Current Epic 3 pattern is additive and contract-preserving: each story hardens one layer and avoids destabilizing prior story behavior.
- Story 3.3 should keep this pattern: minimal-risk extension of existing Spark ingestion paths with clear tests and documentation updates.

### Latest Tech Information

- Spark Structured Streaming (Spark 3.5.x docs): watermark semantics are based on `max event time seen - lateness threshold`; state for a window is retained until watermark passes the window end.
- PySpark `withWatermark` guidance (Spark docs latest): apply watermark before windowed stateful aggregation; use timestamp-typed event-time column.
- Databricks 2026 guidance: watermarks are essential to bound state growth; append mode emits finalized rows only after watermark threshold, while update mode emits changed rows each trigger (sink compatibility required).

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#story-3-3-configure-event-time-semantics-watermarks-and-windows`]
- [Source: `_bmad-output/planning-artifacts/prd.md#stream-processing--storage`]
- [Source: `_bmad-output/planning-artifacts/prd.md#technical-success`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#data-architecture`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#implementation-patterns--consistency-rules`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#project-structure--boundaries`]
- [Source: `_bmad-output/implementation-artifacts/3-2-ingest-and-validate-events-with-spark-structured-streaming.md`]
- [Source: `config/spark_jobs.yaml`]
- [Source: `stream_analytics/spark_jobs/ingestion.py`]
- [External Source: Spark Structured Streaming Programming Guide 3.5.x]
- [External Source: PySpark `DataFrame.withWatermark` API docs (latest)]
- [External Source: Databricks Structured Streaming watermark/output mode guidance (updated 2026)]

## Dev Agent Record

### Agent Model Used

GPT-5.3 (Cursor create-story workflow)

### Debug Log References

- Log watermark/window configuration at streaming query startup (`watermark_delay`, `window_duration`, `window_slide`, output mode, checkpoint path).
- Log per-trigger counts and late-data handling indicators where available to support AC #2 evidence.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story context includes architecture constraints, prior-story learnings, and watermark/output-mode caveats needed to avoid incorrect Spark semantics.
- Story is prepared for implementation with explicit anti-regression and anti-reinvention guardrails.
- Implemented canonical `event_time_ts` UTC conversion from microsecond `event_time` and preserved raw event-time for debugging.
- Added typed watermark/window config contract (`watermark_delay`, `window_duration`, `window_slide`, `window_output_mode`) with fail-fast duration validation.
- Added explicit windowed aggregation foundations with `.withWatermark(...)` and canonical output fields `window_start`/`window_end`.
- Added structured observability logs for startup and per-batch late-data evidence (accepted-late vs too-late dropped where measurable).
- Added deterministic tests for config validation and watermark boundary behavior; full Spark jobs test module passes.
- Code review fixes applied: set Spark SQL session timezone to UTC during streaming job startup to make event-time conversion deterministic.
- Code review fixes applied: observability now logs both estimated late-data counts and actual `numRowsDroppedByWatermark` from stateful query progress when available.
- Code review fixes applied: replaced per-batch driver-side full event-time collection with aggregate-based Spark computations for observability summaries.
- Code review fixes applied: added tests for UTC timezone startup configuration and watermark-drop metric extraction from query progress.

### File List

- `_bmad-output/implementation-artifacts/3-3-configure-event-time-semantics-watermarks-and-windows.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `config/spark_jobs.yaml`
- `stream_analytics/spark_jobs/config_models.py`
- `stream_analytics/spark_jobs/ingestion.py`
- `stream_analytics/spark_jobs/windowing.py`
- `tests/spark_jobs/test_ingestion_config_and_validation.py`
- `README.md`
- `docs/design_note.md`

## Change Log

- 2026-04-14: Implemented Story 3.3 event-time conversion, watermark/window config + validation, windowed foundations, late-data observability logs, and deterministic tests.
- 2026-04-14: Senior AI review fixes applied for watermark observability fidelity, UTC session timezone enforcement, and test coverage hardening.

## Senior Developer Review (AI)

### Reviewer

Javi

### Date

2026-04-14

### Outcome

Changes Requested -> Resolved

### Findings and Resolution

- HIGH: Late-data observability metrics were potentially misleading because they did not include Spark state-operator watermark-drop metrics.
  - Resolved by logging `dropped_by_watermark_rows` from `lastProgress.stateOperators[].numRowsDroppedByWatermark` for the corresponding windowed query.
- HIGH: UTC semantics were not explicitly enforced at Spark session level for event-time conversion paths.
  - Resolved by setting `spark.sql.session.timeZone = UTC` at streaming job startup.
- MEDIUM: Observability used full `collect()` of batch event-time values.
  - Resolved by replacing with aggregate computations (`max`, `count`, conditional sums) and collecting only summary rows.
- MEDIUM: Tests did not validate timezone/session configuration or watermark-drop metric extraction wiring.
  - Resolved by adding focused tests for timezone setting and watermark progress metric parsing.
