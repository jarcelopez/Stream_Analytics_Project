# Story 3.4: Compute and Store Windowed KPIs and Advanced Metrics

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,  
I want Spark jobs that compute windowed KPIs and at least one stateful/anomaly metric,  
so that downstream dashboards can show both basic performance and stressed/anomalous behavior.

## Acceptance Criteria

1. Given clean, structured streams from ingestion, when I run the KPI and analytics Spark jobs, then they output a denormalized Parquet dataset (for example `metrics_by_zone_restaurant_window`) with keys like `zone_id`, `restaurant_id`, `window_start`, and `window_end`.
2. Given the PRD requirements for basic, intermediate, and advanced metrics, when I inspect the metrics dataset, then I can find columns for core KPIs (for example active orders, average delivery time, cancellation rate) and at least one anomaly or stress index metric per zone/restaurant/time window.

## Tasks / Subtasks

- [x] Task 1 (AC: #1): Create canonical KPI aggregation module and outputs
  - [x] Add `stream_analytics/spark_jobs/windowed_kpis.py` that consumes validated streaming records and computes KPI windows with `event_time_ts`.
  - [x] Reuse existing watermark/window config from `SparkIngestionConfig` (`watermark_delay`, `window_duration`, `window_slide`, `window_output_mode`) and do not introduce parallel config paths.
  - [x] Produce canonical fields for denormalized output: `zone_id`, `restaurant_id`, `window_start`, `window_end`, `active_orders`, `avg_delivery_time_seconds`, `cancellation_rate`, `total_orders`.
- [x] Task 2 (AC: #1, #2): Implement intermediate stateful metric logic
  - [x] Add an intermediate metric using stateful/windowed semantics (for example `orders_per_active_courier` or rolling completion-efficiency score) grouped by `zone_id`, `restaurant_id`, and time window.
  - [x] Ensure the metric remains computable with currently available feed fields (`order_events`, `courier_status`) without requiring schema contract changes.
- [x] Task 3 (AC: #2): Implement at least one advanced anomaly/stress metric
  - [x] Add `stream_analytics/spark_jobs/anomaly_scores.py` and/or `stream_analytics/spark_jobs/zone_stress_index.py` to compute an advanced metric aligned with PRD/architecture guidance.
  - [x] Ensure anomaly metric handles late events consistently with Story 3.3 watermark semantics and avoids unbounded state.
  - [x] Include explicit threshold or scoring columns needed for Story 4.3 health/anomaly dashboard consumption.
- [x] Task 4 (AC: #1): Persist curated denormalized dataset to Parquet
  - [x] Write streaming output to a configured Parquet sink path with checkpoint isolation for metrics jobs.
  - [x] Use append/update output mode compatible with chosen sink semantics and watermark strategy.
  - [x] Keep dataset naming and columns in snake_case; use canonical dataset name `metrics_by_zone_restaurant_window`.
- [x] Task 5 (AC: #1, #2): Documentation and schema contract updates
  - [x] Update `docs/design_note.md` with metric definitions, formulas, field-level semantics, and how each maps to basic/intermediate/advanced use cases.
  - [x] Update `README.md` with "how to run and inspect metrics output" steps, including Parquet location and a sample query.
- [x] Task 6 (AC: #1, #2): Add deterministic tests and guardrails
  - [x] Add tests under `tests/spark_jobs/` validating KPI calculations, anomaly/stress calculations, and expected output schema columns.
  - [x] Add tests to verify late data inside watermark is included and too-late data is excluded from stateful KPI/anomaly paths.
  - [x] Add regression checks to ensure Story 3.2/3.3 ingestion and watermark contracts remain stable.

## Dev Notes

- Story and dependency context:
  - This story builds directly on Story `3.2` (`stream_analytics/spark_jobs/ingestion.py`) and Story `3.3` (`stream_analytics/spark_jobs/windowing.py`) contracts.
  - Existing inputs already include typed event-time field `event_time_ts`, watermark/window config, and valid/invalid split with reason-coded error sink.
  - Story `3.5` depends on this story's curated metrics outputs for inspection, and Epic 4 depends on these fields for dashboard KPIs/filters/anomaly view.
- Existing implementation intelligence from Story 3.3:
  - Watermark/window config is validated in `stream_analytics/spark_jobs/config_models.py`; reuse this model.
  - Ingestion currently creates memory sinks (`order_events_valid`, `courier_status_valid`, `order_events_windowed_kpis`, `courier_status_windowed_kpis`) and observability logging for late-event behavior.
  - UTC event-time semantics are explicitly enforced (`spark.sql.session.timeZone=UTC`), and must be preserved.
- Architecture guardrails that MUST be followed:
  - Keep modules under `stream_analytics/spark_jobs/`; shared utilities under `stream_analytics/common/`.
  - Keep snake_case everywhere (`dataset`, columns, logs, config keys).
  - Preserve canonical window columns `window_start` and `window_end`.
  - Preserve status artifact contract (`status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`) and status enum values.
- Technical requirements and anti-reinvention guidance:
  - Reuse existing config loader (`stream_analytics/common/config.py`) and structured logging helpers.
  - Do not reimplement Event Hubs ingestion, payload validation, or timestamp conversion logic.
  - Prefer composing KPI/anomaly transforms from validated streams already produced by ingestion path.
  - Keep output contract denormalized and dashboard-ready to avoid duplicate downstream joins.
- Risks and pitfalls to prevent:
  - Incorrect KPI math due to mixed event-time and processing-time semantics.
  - State blow-up from missing/incorrect watermark application in stateful metrics.
  - Sink mismatch (`update` mode with incompatible file sink strategy) causing stale or duplicate metric rows.
  - Breaking Story 4 filter requirements by omitting `zone_id`, `restaurant_id`, `window_start`, `window_end`.
  - Hidden regression to Story 3.2 error routing or Story 3.3 watermark observability.

### Project Structure Notes

- Preferred code placement:
  - KPI job logic: `stream_analytics/spark_jobs/windowed_kpis.py`
  - Advanced metric logic: `stream_analytics/spark_jobs/anomaly_scores.py` and/or `stream_analytics/spark_jobs/zone_stress_index.py`
  - Config extensions only if needed: `stream_analytics/spark_jobs/config_models.py` and `config/spark_jobs.yaml`
  - Shared math/helpers only when reused: `stream_analytics/common/`
  - Tests: `tests/spark_jobs/test_windowed_kpis.py` and `tests/spark_jobs/test_anomaly_zsi.py`
- Keep dashboard rendering concerns out of this story; this story owns streaming metric computation and curated storage contracts.

### Previous Story Intelligence

- Story `3.3` already implemented deterministic watermark and UTC time semantics; KPI/anomaly jobs must not bypass `event_time_ts`.
- Story `3.3` observability already captures late-data metrics and dropped-by-watermark evidence; extend rather than replace.
- Story `3.3` used additive, contract-preserving changes; keep the same pattern and avoid broad refactors.

### Git Intelligence Summary

- Recent commits (`story 3.1`, `story 3.2`, `story 3.3`) follow small, incremental story-based delivery.
- Core Spark files already active in Epic 3: `stream_analytics/spark_jobs/ingestion.py`, `stream_analytics/spark_jobs/windowing.py`, `stream_analytics/spark_jobs/config_models.py`, plus matching test files and docs.
- Continue this pattern: implement KPI/anomaly layers as additive modules with focused tests and docs updates.

### Latest Tech Information

- Spark Structured Streaming guidance (Spark docs 3.5.x and Databricks docs updated 2026):
  - Apply `withWatermark` on event-time columns before stateful window/group operations to bound state.
  - `append` mode emits finalized windows after watermark threshold; `update` mode emits changed aggregates each trigger.
  - For stateful streams with joins/aggregations, explicit watermarking on each input stream is strongly recommended to avoid unbounded state and stale outputs.
- Practical implication for this story:
  - If writing to Parquet file sinks, prefer semantics that avoid repeated row rewrites unless an upsert-capable sink strategy is introduced.
  - Keep watermark delay tuned to realistic late-event distribution from generator edge-case settings.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#story-3-4-compute-and-store-windowed-kpis-and-advanced-metrics`]
- [Source: `_bmad-output/planning-artifacts/prd.md#stream-processing--storage`]
- [Source: `_bmad-output/planning-artifacts/prd.md#technical-success`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#data-architecture`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#implementation-patterns--consistency-rules`]
- [Source: `_bmad-output/implementation-artifacts/3-3-configure-event-time-semantics-watermarks-and-windows.md`]
- [Source: `stream_analytics/spark_jobs/ingestion.py`]
- [Source: `stream_analytics/spark_jobs/windowing.py`]
- [Source: `stream_analytics/spark_jobs/config_models.py`]
- [Source: `config/spark_jobs.yaml`]
- [External Source: Spark Structured Streaming Programming Guide 3.5.x]
- [External Source: Databricks watermarks and output mode guidance, updated 2026]

## Dev Agent Record

### Agent Model Used

GPT-5.3 (Cursor create-story workflow)

### Debug Log References

- Reuse structured logging conventions from `stream_analytics/common/logging_utils.py`.
- Log KPI job startup config (`watermark_delay`, `window_duration`, `window_slide`, output mode, checkpoint/sink paths).
- Log batch-level aggregation evidence for KPI/anomaly streams to support verification and grading.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story context includes architecture constraints, previous-story learnings, recent git patterns, and latest watermark/output guidance.
- Story status set to ready-for-dev for dev-story implementation.
- Implemented canonical KPI window aggregation in `stream_analytics/spark_jobs/windowed_kpis.py` with event-time watermark + window semantics.
- Added intermediate capacity metric `orders_per_active_courier` and preserved denormalized keys (`zone_id`, `restaurant_id`, `window_start`, `window_end`).
- Added advanced anomaly/stress scoring in `stream_analytics/spark_jobs/anomaly_scores.py` with explicit threshold fields (`stress_threshold`, `is_stressed`).
- Integrated Parquet sink persistence to `metrics_by_zone_restaurant_window` with isolated checkpoint path and append-mode safety fallback for file sinks.
- Expanded docs (`README.md`, `docs/design_note.md`) and added deterministic Spark-job tests for KPI calculations and output-mode guardrails.
- Validation completed with `pytest tests/spark_jobs -q` (17 passed).
- Code review fixes applied: added deterministic anomaly score unit tests and KPI→anomaly streaming wiring test coverage.
- Configuration contract clarified: `window_output_mode` now explicitly append-only for Parquet metrics sink semantics.
- Validation rerun with `pytest tests/spark_jobs -q` (20 passed).

### File List

- `_bmad-output/implementation-artifacts/3-4-compute-and-store-windowed-kpis-and-advanced-metrics.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `config/spark_jobs.yaml`
- `stream_analytics/spark_jobs/config_models.py`
- `stream_analytics/spark_jobs/ingestion.py`
- `stream_analytics/spark_jobs/windowed_kpis.py`
- `stream_analytics/spark_jobs/anomaly_scores.py`
- `tests/spark_jobs/test_ingestion_config_and_validation.py`
- `tests/spark_jobs/test_windowed_kpis_and_anomaly.py`
- `README.md`
- `docs/design_note.md`

## Senior Developer Review (AI)

### Reviewer

Javi (AI Code Review Workflow)

### Date

2026-04-14

### Outcome

Approved after fixes. High/medium findings were addressed in code and tests.

### Findings Resolved

- Added deterministic anomaly/stress scoring validation via `compute_zone_stress_values` and corresponding tests.
- Added integration-style ingestion test validating KPI/anomaly/Parquet wiring in `run_ingestion_streaming_job`.
- Clarified output mode contract so metrics file sink behavior is explicit (`append` only in config model).

## Change Log

- 2026-04-14: Story reviewed and fixed based on adversarial code-review findings; status moved to done.
