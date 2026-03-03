# Story 1.5: Run the Generator in Debug Mode

Status: done

## Story

As a Student/Developer,
I want a low-volume debug mode with capped throughput and entity counts,
so that I can reliably reproduce scenarios end-to-end in under a minute using a documented debug flag.

## Acceptance Criteria

1. **Debug mode configuration and behavior**
   - Given a documented debug configuration option (for example `mode=debug` or an equivalent flag),
   - When I start the generator in debug mode,
   - Then the generator limits throughput to a low, documented maximum (for example ≤ 100 events per second) and caps entity counts (for example ≤ 20 restaurants and ≤ 20 couriers).

2. **Debug demo run for Milestone 1**
   - Given I run the generator in debug mode using the documented command,
   - When I follow the documented steps to generate capped JSON/AVRO batches for both feeds,
   - Then a representative scenario (including at least one edge case when non-zero edge-case rates are configured) completes in roughly one minute on a typical laptop, suitable for quick iteration and troubleshooting, and these debug batches can later be wired into the full streaming pipeline and dashboard in Milestone 2.

## Tasks / Subtasks

- [x] Implement debug mode configuration
  - [x] Add debug-mode flags and configuration fields (for example `mode: debug`, max throughput, and capped entity counts) in `config/generator.yaml` and/or CLI options.
  - [x] Wire debug configuration into generator startup so that debug mode can be enabled without code changes.
- [x] Enforce capped throughput and entity counts in debug mode
  - [x] Update generator logic to cap restaurants and couriers (for example ≤ 20 restaurants and ≤ 20 couriers) when debug mode is enabled.
  - [x] Implement a simple rate limiter or pacing mechanism that keeps total event throughput under the documented debug maximum (for example ≤ 100 events per second).
  - [x] Ensure both order-events and courier-status feeds honor the debug-mode caps consistently.
-- [x] Ensure representative edge cases appear in debug mode
  - [x] Reuse existing edge-case configuration (late events, duplicates, missing steps, impossible durations, courier offline) so that at least one edge case is very likely to appear during a short debug run when non-zero rates are configured.
  - [x] Validate that edge-case flags/rates work correctly under the lower-throughput, smaller-entity debug configuration.
- [x] Document how to run the generator in debug mode
  - [x] Add a clearly labeled “Debug mode” section to the Milestone 1 README and/or demo runbook that explains prerequisites, commands, and expected behavior.
  - [x] Include example debug configuration snippets and sample commands for both file and streaming modes (if both are supported).
  - [x] Describe expected run time (≈ 1 minute) and what a grader should see in logs, sample outputs, and the dashboard when debug mode is enabled.
- [x] Validate debug demo run for Milestone 1
  - [x] Run the generator in debug mode and confirm that capped entity counts are in effect (for example via logs or small sample counts) and that a small debug batch is produced quickly.
  - [x] Add and maintain generator-level debug demo tests that exercise dual-feed generation, entity caps, and edge-case visibility (see `tests/generator/test_debug_demo_pipeline.py`).
  - [ ] Wire the full streaming pipeline (generator → Event Hubs → Spark Structured Streaming → Parquet → Streamlit dashboard) to consume debug batches and validate an end-to-end under-a-minute demo in Milestone 2.
  - [ ] Verify in the dashboard that at least one edge-case scenario is observable in the downstream metrics and/or dashboard views during a debug-mode run once streaming jobs and the UI are implemented.

## Dev Notes

- **Relevant requirements and epics**
  - This story directly implements FR32 (“run the generator in a debug mode that limits throughput to a configurable maximum and caps entity counts”) and contributes to FR33 (edge-case inspection) and FR31 (reproducible demo runs).
  - It belongs to Epic 1 “Design and Run Synthetic Food‑Delivery Feeds” and should be consistent with Stories 1.1–1.4 (core parameters, dual feeds, edge-case toggles, and sample batches), as described in `epics.md`.
- **Architecture and project-structure alignment**
  - Keep all generator changes within the `generator/` package (for example `config_models.py`, `base_generators.py`, `edge_cases.py`, and `cli.py`) and respect the shared `config/` and `common/` modules defined in the architecture document.
  - Maintain the unified naming conventions: snake_case everywhere for fields and JSON keys, and use existing IDs (`order_id`, `courier_id`, `zone_id`, etc.) so that debug runs remain compatible with Spark schemas and downstream analytics.
- **Debug mode semantics**
  - Debug mode is a configuration overlay, not a separate code path: the same generator code should work for both normal and debug runs, with debug mode applying stricter caps on entities and throughput plus any extra flags needed to guarantee that at least one edge case appears quickly.
  - Ensure that debug mode can be enabled from both CLI and configuration files without code edits, and that any debug-only defaults are clearly documented and safe to run repeatedly.
- **Observability and verification**
  - Use the project’s structured logging pattern (JSON lines with `timestamp`, `component`, `level`, `message`, and `details`) to expose debug-mode settings, actual entity counts, and observed throughput so that graders can verify FR32.
  - If status/heartbeat artifacts such as `generator_status.json` already exist, include a `debug_mode` flag and any relevant counters to make debug runs visible on the dashboard’s Debug/Status page.
- **Downstream compatibility**
  - Confirm that debug-mode events still conform to the AVRO schemas and PRD expectations so that Spark jobs, analytics metrics, and the Streamlit dashboard do not require any special debug-only logic.
  - Use debug-mode runs to quickly exercise edge-case behaviors needed later for watermarks, windowing, anomaly metrics, and NFR checks (for example end-to-end latency under 15 seconds).

### Project Structure Notes

- Align generator code, configuration, and logging with the architecture document’s structure (for example `generator/`, `spark_jobs/`, `dashboard/`, `common/`, and `config/` folders) so that future stories can reuse the same patterns.
- Ensure any new debug-related files (for example debug-specific configs or sample outputs) live in predictable, documented locations and do not conflict with existing sample or production-like data paths.

### References

- Story definition and acceptance criteria: `_bmad-output/planning-artifacts/epics.md` (Story 1.5).
- Functional and non-functional requirements: `_bmad-output/planning-artifacts/prd.md` (FR32 and related FRs, NFR1/NFR5/NFR6).
- Architecture and project structure guidance: `_bmad-output/planning-artifacts/architecture.md`.

## Dev Agent Record

### Agent Model Used

Cursor Dev Agent (GPT-5.1)

### Debug Log References

- Generator debug-mode runs should be visible in structured logs (for example `logs/generator.log`) and any status artifacts under `status/`.
- CLI-level debug runs log effective entity caps and `events_per_second` values via `component="generator_cli"` and generator-edge-case behavior via `component="generator_edge_cases"` for FR32 verification.

### Completion Notes List

- Story file created with context from PRD, epics, and architecture documents, emphasizing debug-mode semantics, observability, and end-to-end demo alignment.
- Implemented generator debug-mode behavior by clamping entity counts and effective throughput in `stream_analytics.generator.cli`, added regression tests around the debug caps, and expanded the README “Debug/sample runs and edge cases” section for Story 1.5.
- Tightened debug-mode configuration handling by centralizing cap clamping logic and added tests to verify both cap enforcement and seeding behavior for reproducible debug runs; generator-level debug-demo tests now cover capped entity counts, effective debug throughput configuration, and edge-case visibility for teaching runs, with full streaming and dashboard validation deferred to Milestone 2 stories.

### Change Log

- Implemented `tests/generator/test_debug_demo_pipeline.py` to exercise a full debug demo run using the real configuration and verify both feeds produce small JSON batches suitable for a quick pipeline.
- Expanded the README with an “End-to-end debug demo (AC2)” section that documents how to run the generator in debug mode and how those batches flow through the future streaming pipeline and dashboard.
- Extended `tests/generator/test_debug_demo_pipeline.py` with a debug-mode edge-case scenario that enables non-zero edge-case rates in the generator configuration and asserts that OFFLINE courier statuses and impossible delivery durations appear in the capped debug sample batches.

### File List

- `_bmad-output/implementation-artifacts/1-5-run-the-generator-in-debug-mode.md`
- `stream_analytics/generator/cli.py`
- `tests/generator/test_cli_config_integration.py`
- `tests/generator/test_debug_demo_pipeline.py`
- `README.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `samples/generator/order_events/json/sample.jsonl`
- `samples/generator/courier_status/json/sample.jsonl`
- `samples/generator/order_events/avro/sample.avro`
- `samples/generator/courier_status/avro/sample.avro`
