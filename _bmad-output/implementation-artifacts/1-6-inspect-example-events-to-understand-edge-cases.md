# Story 1.6: Inspect Example Events to Understand Edge Cases

- **Story ID:** 1.6
- **Story Key:** 1-6-inspect-example-events-to-understand-edge-cases
- **Epic:** Epic 1 – Design and Run Synthetic Food‑Delivery Feeds
- **Source FRs:** FR32, FR33 (plus related streaming correctness FRs)
- **Status:** done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,
I want to easily inspect example events and schemas for each edge case,
so that I can see exactly how late/out-of-order, duplicate, missing-step, and impossible-duration scenarios are encoded.

## Acceptance Criteria

1. **Edge-case examples are discoverable and complete**
   - Given the generator documentation, epics, and PRD,
   - When I look up each supported edge‑case type (late/out‑of‑order events, duplicates, missing‑step sequences, impossible durations, and courier‑offline scenarios),
   - Then I can find at least one concrete example event (or short sequence of events) that demonstrates how that edge case is represented in the data for both order events and courier status where applicable.

2. **Examples conform to schemas and clearly illustrate semantics**
   - Given the AVRO and JSON schemas for order events and courier status,
   - When I validate the curated example events against those schemas,
   - Then all examples conform to the schemas and clearly illustrate the intended edge‑case semantics (for example which fields / combinations indicate lateness, duplicates, missing steps, impossible durations, or courier offline behavior).

3. **Examples are easy to run and reproduce from configs**
   - Given the existing generator configuration (including debug mode from Story 1.5),
   - When I follow the documented steps to run the generator in sample or debug mode using the provided configs,
   - Then I can reliably reproduce the same categories of example events (edge cases plus “normal” events) within a short run, without editing generator code.

4. **Documentation connects edge cases to downstream analytics**
   - Given the curated examples and the PRD/architecture requirements for watermarks, windows, anomaly metrics, and Zone Stress Index,
   - When I read the documentation section for this story,
   - Then it explains how each edge‑case encoding is expected to show up in downstream Spark jobs and dashboard metrics (for example which fields feed Delivery Time Anomaly Score and Zone Stress Index, and how late/duplicate events should affect those metrics).

## Tasks / Subtasks

- [x] Curate edge‑case example events (AC: 1, 2)
  - [x] Use existing generator sample/debug runs to collect representative JSON/AVRO events for each edge case (late/out‑of‑order, duplicates, missing‑step, impossible durations, courier‑offline).
  - [x] Store small, human‑readable slices of these examples under a documented path (for example `samples/generator/*/edge_cases/`) without creating huge files.
  - [x] Add inline comments or adjacent markdown explaining why each example qualifies as that edge case (referencing key fields like `event_time`, status transitions, and IDs).
- [x] Validate examples against schemas (AC: 2)
  - [x] Confirm that curated examples validate against the AVRO schemas in `stream_analytics/generator/schemas/` and any Spark‑side schemas in `stream_analytics/spark_jobs/schemas.py`.
  - [x] Add or update simple validation utilities/tests (for example in `tests/generator/` or `tests/spark_jobs/`) that read the curated examples and assert schema compliance.
- [x] Wire examples to configs and debug mode (AC: 3)
  - [x] Ensure there is at least one documented generator configuration (for example in `config/generator.yaml`) that reliably produces each edge case in a short debug run, building on Story 1.5’s debug‑mode semantics.
  - [x] Update the README or design note to show which config settings to use to reproduce each curated example set (including any seeds or debug flags).
- [x] Document downstream interpretation (AC: 4)
  - [x] Add a concise documentation section (for example in `docs/design_note.md` or a dedicated `docs/edge_cases.md`) that maps each edge‑case encoding to the expected behavior in Spark Structured Streaming jobs and dashboard metrics.
  - [x] Cross‑reference relevant PRD FRs (FR33, FR34, FR35) and architecture sections so future code changes can be checked against this contract.

## Dev Notes

- **Relevant requirements and epics**
  - Implements and deepens FR33 (“inspect example events and schemas to understand how edge cases are encoded”) and supports FR32, FR34, and FR35 by making edge‑case behavior intentional and inspectable.
  - Anchored in Epic 1 “Design and Run Synthetic Food‑Delivery Feeds”, Story 1.6 in `_bmad-output/planning-artifacts/epics.md`, and should remain consistent with Stories 1.3 (edge‑case toggles), 1.4 (sample batches), and 1.5 (debug mode).
- **Source tree components to touch**
  - Generator: `stream_analytics/generator/` (especially `edge_cases.py`, `serialization.py`, `config_models.py`, and any helpers used to emit debug/sample data).
  - Samples: `samples/generator/order_events/*` and `samples/generator/courier_status/*` as the primary place to land curated example snippets, keeping file sizes small and focused.
  - Schemas: AVRO schemas under `stream_analytics/generator/schemas/` and Spark schemas in `stream_analytics/spark_jobs/schemas.py` for validation.
  - Documentation: `docs/design_note.md`, PRD (`_bmad-output/planning-artifacts/prd.md`), and epics (`_bmad-output/planning-artifacts/epics.md`) for cross‑references.
- **Testing standards summary**
  - Add or extend tests under `tests/generator/` and/or `tests/spark_jobs/` to:
    - Validate curated examples against AVRO and Spark schemas.
    - Assert that debug/sample configs still generate events compatible with downstream Spark jobs and dashboard aggregations.
    - Guard against regressions where edge‑case encodings change silently (for example missing flags or changed field semantics).
  - Follow the project’s structured logging and status‑artifact patterns so that edge‑case inspection remains visible via `logs/` and `status/` where applicable.

### Project Structure Notes

- **Alignment with unified project structure**
  - Keep generator, Spark jobs, dashboard, and docs within the structure defined in `architecture.md` (for example `stream_analytics/generator/`, `stream_analytics/spark_jobs/`, `stream_analytics/dashboard/`, `stream_analytics/common/`, `config/`, `docs/`, `samples/`).
  - Maintain snake_case for all dataset, column, and JSON field names (for example `order_id`, `courier_id`, `zone_id`, `event_time`, `window_start`, `window_end`, `zone_stress_index`).
- **Detected conflicts or variances**
  - If new example files or helper scripts diverge from the documented patterns (for example different naming or alternate sample locations), document the rationale and update `architecture.md` or the README to keep future stories aligned.

### References

- Story definition and acceptance criteria: `_bmad-output/planning-artifacts/epics.md` (Story 1.6).
- Functional and non‑functional requirements: `_bmad-output/planning-artifacts/prd.md` (FR32–FR35, NFR1, NFR5, NFR6).
- Architecture and project structure guidance: `_bmad-output/planning-artifacts/architecture.md`.
- Existing generator samples used as a baseline:
  - `samples/generator/order_events/json/sample.jsonl`
  - `samples/generator/courier_status/json/sample.jsonl`
  - `samples/generator/order_events/avro/sample.avro`
  - `samples/generator/courier_status/avro/sample.avro`

## Developer Context and Guardrails

- **Technical requirements**
  - Edge‑case encodings must remain consistent with PRD expectations so that Spark jobs can implement correct watermarks, windows, and anomaly metrics.
  - Example sets should be small enough for quick inspection but rich enough to demonstrate all configured behaviors (late/out‑of‑order, duplicate, missing‑step, impossible‑duration, courier‑offline).
- **Architecture compliance**
  - Ensure curated examples and any helper code do not bypass the agreed patterns for schemas, logging, or project layout described in `architecture.md`.
  - Treat AVRO schemas as the single source of truth for event structure and keep example encodings aligned with them.
- **Library and framework requirements**
  - PySpark Structured Streaming: when referencing downstream behavior, assume current Spark 3.5–series semantics for `withWatermark` and window aggregations (event‑time column + delay threshold) so examples can be used directly in tests/jobs.
  - Azure Event Hubs: examples and docs should assume the Python `azure-eventhub` client with batched sends and partition‑key strategies as defined in ingestion stories.
  - Streamlit: any dashboard snippets linked from this story should assume `st.cache_data`‑based caching for reading Parquet metrics, consistent with Streamlit 1.x guidance.
- **File structure requirements**
  - Place new curated example files under `samples/` (not mixed with production configs) and keep paths and names descriptive (for example `edge_case_late_events.jsonl`).
  - Ensure any new docs live under `docs/` and are linked from the main README or design note for discoverability.
- **Testing requirements**
  - Add schema‑validation tests for curated examples and keep them lightweight enough to run in the standard test suite.
  - Where possible, add a focused streaming test that consumes a curated example set into a minimal Spark job and asserts expected behavior for at least one window + watermark scenario.

## Previous Story Intelligence (Story 1.5)

- Story 1.5 (`_bmad-output/implementation-artifacts/1-5-run-the-generator-in-debug-mode.md`) established:
  - A debug mode with capped throughput and entity counts, driven by `config/generator.yaml` and CLI options.
  - Structured logging and (optionally) status artifacts (for example `logs/generator.log`, `status/generator_status.json`) that expose debug settings and effective behavior.
  - Tests and documentation that validate debug runs and make them reproducible.
- This story should:
  - Reuse debug mode as the primary way to generate reproducible, inspectable edge‑case examples.
  - Avoid introducing separate code paths for “inspection only” runs—debug/sample configs should exercise the same generator logic used for full demos.
  - Extend tests and docs from Story 1.5 rather than duplicating them in new locations.

## Git Intelligence Summary

- Recent commits (`implementation 1.1` through `implementation 1.5`) have:
  - Established the core generator behavior, edge‑case toggles, sample batches, and debug mode semantics.
  - Introduced structured logging and status artifacts that will be reused when inspecting edge‑case examples.
- When implementing this story:
  - Follow existing patterns used in Stories 1.1–1.5 for where to put code, tests, and docs.
  - Prefer small, additive changes over rewrites, so that git history continues to tell a coherent story across the Epic 1 implementation.

## Latest Technical Information (for reference)

- **PySpark Structured Streaming**
  - Use `withWatermark("event_time", "<delay>")` in downstream jobs so late events beyond the configured delay are eventually dropped and window state can be cleaned up.
  - Window aggregations should group by `window(event_time, "<size>")` (and optionally slide) and may use the curated examples from this story to test late/duplicate behavior.
- **Azure Event Hubs Python client**
  - Use the modern `azure-eventhub` client (5.x) with batched sends and, where applicable, partition keys aligned with `order_id`, `courier_id`, or `zone_id`.
  - Prefer configuration‑driven connection settings and, for production‑style runs, Azure Identity–based auth; for course demos, connection strings may still be used but should be kept out of committed configs.
- **Streamlit dashboard**
  - Use `st.cache_data` to cache metric DataFrame loads from Parquet, with a small `ttl` so edge‑case behaviors become visible within the PRD’s < 15s latency target while keeping the dashboard responsive.

## Project Context Reference

- PRD: `_bmad-output/planning-artifacts/prd.md` (streaming correctness, edge cases, watermarks, and NFRs).
- Architecture: `_bmad-output/planning-artifacts/architecture.md` (project structure, datasets, logging, and orchestration).
- Epics and stories: `_bmad-output/planning-artifacts/epics.md` (Epic 1 stories 1.1–1.6 and their relationships).
- Use these documents as the canonical reference when making implementation decisions or refining examples.

## Story Completion Status

- **Target status:** `ready-for-dev` once:
  - Curated edge‑case examples exist and are validated against schemas.
  - Configs and debug/sample run instructions reliably reproduce those examples.
  - Documentation connects examples to downstream Spark and dashboard behavior.
- **Follow‑ups:** Later stories in Milestone 2 (Spark jobs, metrics, and dashboard) should explicitly reference this story when implementing watermarks, windows, anomaly metrics, and ZSI to ensure that edge‑case encodings are honored end‑to‑end.

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- Detected conflicts or variances (with rationale)

### References

- Cite all technical details with source paths and sections, e.g. [Source: docs/<file>.md#Section]

## Dev Agent Record

### Agent Model Used

Cursor Dev Agent (GPT-5.1)

### Debug Log References

- Generator and edge‑case behavior should be visible via structured logs (for example `logs/generator.log`) and any status artifacts under `status/`, including flags that indicate debug mode and edge‑case configuration.
- Where practical, add log lines that specifically reference curated edge‑case example runs so they can be correlated with documentation and tests.

### Completion Notes List

- Story file created and enriched using PRD, epics, architecture document, and previous Story 1.5 implementation as primary inputs.
- Acceptance criteria expanded to cover curated examples, schema validation, reproducibility via configs/debug mode, and downstream interpretation.
- Developer context, architecture guardrails, and testing expectations captured so the dev agent can implement this story without rediscovering requirements from scratch.
- Initial curated JSON edge‑case slices added for order events and courier status under `samples/generator/*/json/edge_cases/`, covering late/out‑of‑order, duplicate, missing‑step, impossible‑duration, and courier‑offline/mismatch scenarios.
- Schema‑validation tests added in `tests/generator/test_edge_case_example_files_validate_against_schemas.py` to ensure curated edge‑case files remain aligned with the AVRO schemas.
 - Edge-case demo configuration added in `config/generator_edge_cases_demo.yaml` plus `docs/edge_cases.md` to document how to reproduce and interpret each edge-case encoding in downstream Spark jobs and dashboard metrics.

### File List

- `_bmad-output/implementation-artifacts/1-6-inspect-example-events-to-understand-edge-cases.md`
- `_bmad-output/implementation-artifacts/1-5-run-the-generator-in-debug-mode.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `samples/generator/order_events/json/sample.jsonl`
- `samples/generator/courier_status/json/sample.jsonl`
- `samples/generator/order_events/json/edge_cases/order_events_edge_cases.jsonl`
- `samples/generator/courier_status/json/edge_cases/courier_status_edge_cases.jsonl`
- `samples/generator/order_events/avro/sample.avro`
- `samples/generator/courier_status/avro/sample.avro`
- `tests/generator/test_edge_case_example_files_validate_against_schemas.py`
 - `config/generator_edge_cases_demo.yaml`
 - `docs/edge_cases.md`

