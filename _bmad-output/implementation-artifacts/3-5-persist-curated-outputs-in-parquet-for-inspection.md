# Story 3.5: Persist Curated Outputs in Parquet for Inspection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Professor/Grader,  
I want curated Parquet outputs that match the documented schemas and metric definitions,  
so that I can inspect and verify the analytics without reading streaming code.

## Acceptance Criteria

1. Given a successful run of the analytics jobs, when I navigate to the configured Parquet output location, then I see partitioned Parquet files for the metrics dataset and can read them with standard tools (for example Spark, Python, or SQL readers).
2. Given I compare the Parquet schema and contents to the documented metric definitions, when I sample a few windows and entities, then the data matches the expected shapes and semantics (correct types, reasonable value ranges, and consistent aggregation logic).

## Tasks / Subtasks

- [x] Task 1 (AC: #1): Finalize and enforce curated Parquet sink contract
  - [x] Confirm canonical dataset name remains `metrics_by_zone_restaurant_window` and sink path is configuration-driven via `config/spark_jobs.yaml`.
  - [x] Ensure partitioning strategy is explicit and stable for inspection workflows (for example by date/window boundaries) without breaking dashboard read patterns.
  - [x] Keep checkpoint path isolated from data path and document expected directory layout.
- [x] Task 2 (AC: #1, #2): Add schema and semantic validation utilities for grader inspection
  - [x] Add reusable inspection helper(s) under `stream_analytics/spark_jobs/` or `stream_analytics/common/` to read Parquet and assert required columns/types.
  - [x] Validate required keys and time columns: `zone_id`, `restaurant_id`, `window_start`, `window_end`.
  - [x] Validate KPI/anomaly fields produced in Story 3.4 (for example `active_orders`, `avg_delivery_time_seconds`, `cancellation_rate`, stress/anomaly flags and scores).
- [x] Task 3 (AC: #2): Add deterministic tests for Parquet schema and value guardrails
  - [x] Create/extend tests in `tests/spark_jobs/` to assert schema compatibility and non-regression for curated outputs.
  - [x] Add semantic checks for value domains (for example non-negative counts/rates, bounded percentages where defined).
  - [x] Add regression checks to guarantee Story 3.4 output columns remain dashboard-compatible for Epic 4.
- [x] Task 4 (AC: #1, #2): Provide simple grader-facing inspection entrypoints
  - [x] Add one documented Spark/Python inspection example to read the latest curated Parquet output and print schema + sample records.
  - [x] Ensure inspection steps do not require editing source code and work with the documented local/Azure paths.
- [x] Task 5 (AC: #1, #2): Documentation alignment for schema/metric definitions
  - [x] Update `docs/design_note.md` with explicit field-level mapping between metric definitions and Parquet schema.
  - [x] Update `README.md` with a concise "inspect curated Parquet outputs" section for graders (path, command, expected fields).
  - [x] Cross-reference Story 3.4 metric formulas to avoid duplicated or conflicting definitions.

## Dev Notes

- Story and dependency context:
  - This story operationalizes verification of the curated metrics output generated in Story `3.4`.
  - Primary dependency is the existing denormalized output contract from `stream_analytics/spark_jobs/windowed_kpis.py` and anomaly/stress logic already integrated in Epic 3.
  - Epic 4 dashboard stories depend on these outputs remaining schema-stable and semantically correct.
- Existing implementation intelligence from Story 3.4:
  - Story 3.4 already established canonical output naming and key fields (`zone_id`, `restaurant_id`, `window_start`, `window_end`).
  - Watermark/window semantics and UTC handling are already standardized and must remain unchanged for this story.
  - Prior implementation emphasizes additive changes and regression-safe evolution; continue that pattern.
- Architecture guardrails that MUST be followed:
  - Keep Spark processing and persistence logic inside `stream_analytics/spark_jobs/`; shared helpers in `stream_analytics/common/`.
  - Preserve snake_case naming and canonical time-window fields (`window_start`, `window_end`) across code, schema, logs, and docs.
  - Maintain status artifact conventions and do not introduce incompatible structure changes in orchestration/status paths.
- Technical requirements and anti-reinvention guidance:
  - Reuse shared config loader (`stream_analytics/common/config.py`) and existing Spark config models; avoid introducing parallel sink-configuration sources.
  - Reuse existing validated streams and KPI/anomaly outputs instead of re-deriving metrics in a separate code path.
  - Do not create a duplicate "inspection dataset"; validate the existing curated dataset directly to prevent drift.
  - Keep sink + checkpoint semantics aligned with Structured Streaming file-sink constraints.
- Risks and pitfalls to prevent:
  - Silent schema drift that breaks Story 4 filtering and KPI displays.
  - Inconsistent partitioning/checkpoint layout causing unreadable output or duplicate rows during restarts.
  - Mixing processing-time assumptions into event-time-windowed metrics validation.
  - Documentation drift between `README.md`, `docs/design_note.md`, and actual Parquet schema.

### Project Structure Notes

- Preferred code placement:
  - Curated output and sink wiring: `stream_analytics/spark_jobs/windowed_kpis.py`
  - Optional inspection/validation helpers: `stream_analytics/spark_jobs/` or `stream_analytics/common/` (if reused broadly)
  - Config contracts: `stream_analytics/spark_jobs/config_models.py` and `config/spark_jobs.yaml`
  - Tests: `tests/spark_jobs/test_windowed_kpis_and_anomaly.py` plus focused Parquet inspection tests
  - Documentation: `README.md`, `docs/design_note.md`
- Keep dashboard rendering out of this story; this scope is curated persistence correctness and grader-inspection readiness.

### Previous Story Intelligence

- Story `3.4` already captured implementation details and fixes around:
  - append-mode-safe Parquet sink semantics,
  - deterministic anomaly scoring checks,
  - ingestion-to-KPI/anomaly wiring tests,
  - explicit configuration guardrails in `window_output_mode`.
- Preserve those guarantees and extend with inspection/schema-verification coverage rather than modifying core metric formulas.

### Git Intelligence Summary

- Recent commits (`story 3.1`, `story 3.2`, `story 3.3`, `story 3.4`) show a clear pattern of small, story-scoped changes with matching tests/docs.
- Continue this pattern: focused additions for Parquet inspection + schema validation, with minimal impact on existing ingestion/windowing behavior.
- Maintain consistency with existing Epic 3 modules and test organization under `tests/spark_jobs/`.

### Latest Tech Information

- PySpark/Spark Structured Streaming current docs indicate latest stable line at Spark/PySpark `4.1.x`; project can remain on current pinned stack, but code should avoid deprecated patterns and keep migration-friendly APIs.
- Structured Streaming guidance continues to require explicit checkpoint locations for fault recovery; when checkpoint exists, it takes precedence over initial starting position settings.
- Azure Event Hubs Spark connector guidance emphasizes:
  - one consumer group per Spark app/query path where appropriate to avoid receiver conflicts,
  - explicit `checkpointLocation` for reliable restart semantics,
  - tuning `maxEventsPerTrigger` to keep lag bounded and avoid retention-related gaps.
- Practical implication for this story:
  - Keep Parquet inspection deterministic by documenting sink/checkpoint paths and expected lifecycle.
  - Ensure inspection docs mention that data completeness depends on watermark and trigger cadence, not just file presence.

### Project Context Reference

- No `project-context.md` file was detected in this repository. Story context was derived from:
  - `_bmad-output/planning-artifacts/epics.md`
  - `_bmad-output/planning-artifacts/architecture.md`
  - `_bmad-output/planning-artifacts/prd.md`
  - `_bmad-output/implementation-artifacts/3-4-compute-and-store-windowed-kpis-and-advanced-metrics.md`

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#story-3-5-persist-curated-outputs-in-parquet-for-inspection`]
- [Source: `_bmad-output/planning-artifacts/prd.md#stream-processing--storage`]
- [Source: `_bmad-output/planning-artifacts/prd.md#technical-success`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#data-architecture`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#implementation-patterns--consistency-rules`]
- [Source: `_bmad-output/implementation-artifacts/3-4-compute-and-store-windowed-kpis-and-advanced-metrics.md`]
- [Source: `stream_analytics/spark_jobs/windowed_kpis.py`]
- [Source: `stream_analytics/spark_jobs/config_models.py`]
- [Source: `config/spark_jobs.yaml`]
- [External Source: Spark Structured Streaming Programming Guide (latest docs)]
- [External Source: Azure Event Hubs Spark connector structured streaming docs]

## Dev Agent Record

### Agent Model Used

GPT-5.3 (Cursor create-story workflow)

### Debug Log References

- Reuse structured JSON logging conventions from `stream_analytics/common/logging_utils.py`.
- Log sink/checkpoint paths and schema validation outcomes during inspection helpers/tests.
- Keep verification logs concise and reason-coded for grader-friendly troubleshooting.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story context includes architecture constraints, previous-story learnings, recent git patterns, and latest Structured Streaming/Event Hubs guardrails.
- Story status set to `ready-for-dev` for `dev-story` implementation.
- Added explicit parquet persistence inspection contract through reusable helper utilities in `stream_analytics/spark_jobs/parquet_inspection.py`.
- Added grader-facing CLI entrypoint `python -m stream_analytics.spark_jobs.inspect_curated_parquet --path <...>` for schema/sample validation without source edits.
- Enforced explicit parquet partitioning by `window_start` in streaming sink while keeping canonical dataset path `data/metrics_by_zone_restaurant_window`.
- Added deterministic regression and value-domain tests for curated output schema/semantics under `tests/spark_jobs/test_parquet_inspection.py`.
- Updated docs (`README.md`, `docs/design_note.md`, and `config/spark_jobs.yaml` comments) to align schema definitions, inspection workflow, and sink/checkpoint layout guidance.
- Validated changes with `pytest tests/spark_jobs/test_parquet_inspection.py tests/spark_jobs/test_windowed_kpis_and_anomaly.py tests/spark_jobs/test_ingestion_config_and_validation.py` (24 passed).
- Code review fixes (HIGH/MEDIUM): parquet inspector now supports Azure-style URIs without failing local path checks, dependency requirements include parquet inspection stack (`pandas`, `pyarrow`), and tests now cover parquet-read path handling plus CLI empty-dataset flow.

### File List

- `_bmad-output/implementation-artifacts/3-5-persist-curated-outputs-in-parquet-for-inspection.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `stream_analytics/spark_jobs/parquet_inspection.py`
- `stream_analytics/spark_jobs/inspect_curated_parquet.py`
- `stream_analytics/spark_jobs/ingestion.py`
- `tests/spark_jobs/test_parquet_inspection.py`
- `tests/spark_jobs/test_ingestion_config_and_validation.py`
- `config/spark_jobs.yaml`
- `README.md`
- `docs/design_note.md`
- `requirements.txt`

## Change Log

- 2026-04-14: Implemented Story 3.5 parquet inspection contract, schema/value guardrails tests, partitioning/layout documentation, and grader-facing inspection CLI entrypoint.
- 2026-04-14: Addressed code review findings by hardening remote parquet path handling and expanding inspection/CLI coverage.
