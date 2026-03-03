# Story 1.4: Produce Small Sample Batches for Inspection

Status: done

## Story

As a Student/Developer,  
I want to generate small, inspectable sample batches of events,  
so that I can quickly validate event shapes and values before wiring up the full pipeline.

## Acceptance Criteria

1. **Sample mode or capped-batch configuration**
   - Given I run the generator in a documented “sample” mode or with parameters that cap total events,
   - When I request a small batch (for example a few hundred events per feed),
   - Then the generator produces a finite batch of events that can be opened in common tools (text editor, JSON viewer, AVRO decoder) without performance issues.

2. **Schema-aligned sample events**
   - Given I inspect the sample batch,
   - When I compare fields to the documented AVRO/JSON schemas for both feeds,
   - Then each event includes the required fields (for example IDs, event_time, status fields) with reasonable, domain-appropriate values and no schema violations.

3. **Edge-case compatibility**
   - Given edge-case behaviors and rates have been configured via Story 1.3,
   - When I generate sample batches with specific edge cases enabled or disabled,
   - Then the resulting samples are small enough to inspect, still conform to schemas, and clearly reflect the configured edge-case patterns (late/out-of-order, duplicates, missing steps, impossible durations, courier offline).

4. **Downstream readiness**
   - Given the ingestion and analytics Spark jobs assume the schemas and encodings defined in the PRD and architecture,
   - When I later feed these sample batches into the pipeline (file-based or Event Hubs–like test path),
   - Then they can be parsed and processed without schema errors, and their structure is sufficient to test key streaming behaviors (validation, watermarks, windows, anomaly metrics).

5. **Configurable sample size and format**
   - Given I have access to generator configuration (for example `config/generator.yaml` or CLI flags),
   - When I adjust sample size and output format parameters,
   - Then I can generate both JSON and AVRO samples, with clearly documented defaults and safe upper bounds that avoid producing oversized sample files.

## Tasks / Subtasks

- [x] Design sample-mode and capped-batch configuration (AC: 1, 5)
  - [x] Extend the generator configuration model (in `config/generator.yaml` and `GeneratorConfig` or equivalent) with fields such as `sample_mode_enabled`, `sample_total_events_per_feed`, and any related caps that ensure finite batches.
  - [x] Define sensible defaults (for example a few hundred events per feed) and safe maximums to keep sample files small enough for inspection on typical course hardware.
  - [x] Document how sample mode interacts with existing debug mode and edge-case configuration (for example debug mode focuses on throughput/entity caps, while sample mode focuses on finite batch size).

- [x] Implement sample-batch generation path (AC: 1, 2, 5)
  - [x] Add a generator entry point or CLI flag for sample runs (for example `--mode sample` or `--sample-batch`), reusing the main generation logic rather than duplicating it.
  - [x] Ensure both feeds (order events and courier status) can be generated in JSON and AVRO formats in sample runs, honoring existing schema and serialization helpers.
  - [x] Guarantee that sample-mode runs terminate after producing the configured finite batch, with clear logging of counts per feed and output paths.

- [x] Validate schemas and domain values on samples (AC: 2, 3, 4)
  - [x] Add a lightweight validation helper or tests that load sample outputs and confirm they conform to AVRO/JSON schemas (field presence, types, and reasonable domain ranges for IDs, timestamps, and status fields).
  - [x] Confirm that edge-case encodings from Story 1.3 remain valid in sample runs (for example late events still use `event_time` correctly and duplicates/missing steps remain explainable).
  - [x] Where appropriate, add structured logs or counters that show how many events of each feed and edge-case type were produced in a sample run.

- [x] Integrate with architecture conventions and project structure (AC: 3, 4)
  - [x] Place any new code under the existing `generator/` package (for example updating `generator/cli.py`, `base_generators.py`, or related modules), following snake_case naming and the architecture’s package layout.
  - [x] Ensure configuration, logging, and any helpers use the shared utilities described in the architecture document (`common/config.py`, `logging_utils.py`, etc.) rather than introducing ad-hoc patterns.
  - [x] Keep sample output paths and filenames consistent with the project’s naming conventions and directory structure so downstream Spark jobs and docs can reference them easily.

- [x] Documentation and examples (AC: 1, 2, 3, 5)
  - [x] Update the PRD-aligned documentation (for example `docs/design_note.md` and README sections) to describe sample mode, configuration flags, and how to run it.
  - [x] Provide at least one checked-in example of JSON and AVRO sample outputs (small files) that can be used for teaching and debugging.
  - [x] Cross-reference FR6, FR33, and relevant stories (1.3, 1.5, 1.6) so that reviewers can see how sample generation supports debug mode, edge-case inspection, and downstream streaming scenarios.

## Dev Notes

- **Requirements alignment**
  - This story directly implements PRD requirement **FR6** (“produce small sample batches”) and supports **FR33** (inspect example events and schemas) and **FR32** (debug mode) by providing finite, inspectable data slices.
  - It depends on Story 1.1 (core generator parameters), Story 1.2 (two distinct feeds and JSON/AVRO formats), and Story 1.3 (configurable edge-case behaviors) being in place so that samples are representative of real runs.

- **Generator behavior and configuration**
  - Sample mode should be a thin configuration layer over the existing generator, not a separate code path: it should reuse the same schemas, entities, and edge-case logic so that sample behavior matches full runs.
  - When both sample mode and debug mode are available, prefer a clean interaction model such as:
    - Debug mode: clamps throughput and entity counts for short end-to-end demos.
    - Sample mode: clamps total event counts for offline inspection; may also honor debug-mode caps if enabled together.
  - Configuration must be centralized in `config/generator.yaml` (or equivalent) and loaded via the shared config utilities, following the architecture’s guidance on `config/` structure and environment overrides.

- **Architecture and naming guardrails**
  - All data structures and serialized fields in samples must respect the architecture’s naming rules:
    - Snake_case for fields and dataset names (for example `order_id`, `courier_id`, `zone_id`, `event_time`, `delivery_time_seconds`).
    - Future windowed outputs must continue to use `window_start` and `window_end` for time-window boundaries.
  - Sample outputs should be written into locations that are easy to document and stable across runs (for example a dedicated `samples/` subdirectory under a generator output path), so that docs and tests can reference them without guesswork.
  - Maintain consistency with the project structure (`generator/`, `spark_jobs/`, `dashboard/`, `common/`, `tests/`) so that new modules, tests, and scripts land in the expected directories.

- **Observability and teaching value**
  - Follow the architecture’s structured logging pattern (JSON logs with `timestamp`, `component`, `level`, `message`, `details`, and `reason_code` where relevant) when reporting sample generation outcomes.
  - Consider exposing simple counts and edge-case summaries in logs or helper scripts so that a student or grader can quickly see what the sample contains (for example counts per feed, per edge-case type).
  - Align sample batch configuration and defaults with the PRD’s NFRs about demo setup and debug-ability: generating, opening, and inspecting samples should be fast and reliable on course-standard hardware.

- **Interaction with downstream pipeline**
  - Even though this story focuses on sample generation, design outputs so they can be reused later as test fixtures for Spark ingestion and validation jobs (for example, small directories that can be mounted as file-based sources in local tests).
  - Ensure that any assumptions about sample layout (directory names, file extensions, compression) are documented and compatible with the ingestion job design in the architecture document.

### Project Structure Notes

- Keep generator enhancements within the existing `stream_analytics/generator/` and `config/` layout described in the architecture document, with mirrored tests under `tests/generator/`.
- Reuse shared utilities from `stream_analytics/common/` for configuration loading, time handling, and logging; do not introduce new ad-hoc configuration or logging mechanisms for sample mode.
- If new status or log files are introduced to report sample generation, align them with the existing `status/` and `logs/` patterns so that the dashboard’s Debug/Status page can eventually surface this information consistently.

### References

- Epics & stories: `_bmad-output/planning-artifacts/epics.md` – Epic 1, Story 1.4 and related Epic 1 stories.
- PRD: `_bmad-output/planning-artifacts/prd.md` – FR1–FR6, FR32–FR35, and NFRs about setup, latency, and debug-ability.
- Architecture: `_bmad-output/planning-artifacts/architecture.md` – naming conventions, project structure, logging patterns, and generator/Spark/dashboard boundaries.
- Previous story file: `_bmad-output/implementation-artifacts/1-3-control-edge-case-behaviors-via-configuration.md` – edge-case configuration model, debug-mode behavior, and generator observability patterns.

## Dev Agent Record

### Agent Model Used

Cursor Dev Agent – GPT-5.1 (2026-03-03)

### Debug Log References

- Generator sample-mode and capped-batch logs (structured JSON), including per-feed counts and edge-case summaries when enabled.

### Completion Notes List

- Story implemented using the existing generator configuration surface and sample-mode entrypoints, with finite per-feed batches controlled via `sample_batch_size_per_feed` and validated bounds in `GeneratorConfig`.
- Sample-mode and debug-sample CLI paths (`stream_analytics.generator.cli`) generate JSON and AVRO outputs for both feeds, reusing the shared schemas and serialization helpers.
- Edge-case behavior from Story 1.3 remains valid in sample runs, with structured logs exposing counts per feed and per edge-case type to support teaching and debugging.
- Tests in `tests/generator` validate configuration loading, schema-aligned JSON/AVRO samples, edge-case encodings, and debug-mode reproducibility; `pytest` passes with all 16 tests green for this story.
- Story is **implemented and ready for review**, with sprint tracking updated and documentation (`docs/design_note.md`) describing sample mode, configuration flags, and how to run them.

### Senior Developer Review (AI)

- 2026-03-03 – Adversarial code review validated Story 1.4 against the generator configuration, CLI, tests, sample artifacts, and docs.
- File List expanded to include the concrete implementation, tests, docs, and sample output paths used by this story.
- README updated to surface sample and debug-sample usage and to point to `docs/design_note.md` for detailed mapping to FR6/FR33 and related stories.
- JSON and AVRO sample artifacts under `samples/generator/**` are confirmed to be small, inspectable batches suitable for teaching and debugging and intended to be kept under version control.

### File List

- `_bmad-output/implementation-artifacts/1-4-produce-small-sample-batches-for-inspection.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `config/generator.yaml`
- `stream_analytics/generator/config_models.py`
- `stream_analytics/generator/base_generators.py`
- `stream_analytics/generator/serialization.py`
- `stream_analytics/generator/cli.py`
- `tests/generator/test_config_models.py`
- `tests/generator/test_cli_config_integration.py`
- `tests/generator/test_serialization_and_two_feeds.py`
- `docs/design_note.md`
- `samples/generator/order_events/json/sample.jsonl`
- `samples/generator/order_events/avro/sample.avro`
- `samples/generator/courier_status/json/sample.jsonl`
- `samples/generator/courier_status/avro/sample.avro`

### Change Log

- Updated sprint status for `1-4-produce-small-sample-batches-for-inspection` from `ready-for-dev` to `in-progress`, then to `review` after validating implementation and tests.
- Marked all Tasks/Subtasks as complete based on the existing generator implementation, tests, and documentation that already satisfy Story 1.4 acceptance criteria.
