# Story 1.3: Control Edge-Case Behaviors via Configuration

Status: done

## Story

As a Student/Developer,
I want to enable or disable edge-case behaviors (late events, duplicates, missing steps, impossible durations, courier offline) via configuration,
so that I can teach or debug specific streaming scenarios on demand.

## Acceptance Criteria

1. **Edge-case off switch (baseline stream)**
   - Given edge-case toggles and/or rates are defined in generator configuration,
   - When I disable all edge-case flags (or set their rates to 0),
   - Then the generator produces only “normal” events without late, duplicate, missing-step, impossible-duration, or courier-offline behaviors (within documented random variation).

2. **Configurable edge-case rates**
   - Given each supported edge case (late events, duplicates, missing steps, impossible durations, courier offline) has a named configuration field (for example `late_event_rate`, `duplicate_rate`, `missing_step_rate`, `impossible_duration_rate`, `courier_offline_rate`),
   - When I set a non-zero rate for a specific edge case and generate a sufficiently large sample,
   - Then the resulting events include that edge case at approximately the configured frequency, and the encoding of the edge case matches the documented pattern.

3. **Documented encoding for each edge case**
   - Given generator documentation and schemas are available,
   - When I look up a given edge case (for example late delivery or courier offline),
   - Then I can see which fields and values in the JSON/AVRO payload represent that behavior (for example timestamps, flags, status transitions), and those fields conform to the AVRO/JSON schemas defined for the feeds.

4. **Deterministic debug runs**
   - Given I run the generator in debug mode with a fixed seed and specific edge-case configuration,
   - When I re-run the same configuration,
   - Then the distribution and presence of edge cases are stable enough to reproduce teaching/demo scenarios (within any documented randomness guarantees).

5. **Compatibility with downstream streaming jobs**
   - Given the ingestion and analytics Spark jobs assume certain encodings for late/out-of-order events, duplicates, missing steps, impossible durations, and courier offline behavior (per PRD and architecture),
   - When I enable these edge cases in the generator,
   - Then the resulting events can be successfully parsed and processed by the Spark jobs without schema errors, and expected downstream behaviors (late-event handling, duplicate handling, anomaly metrics) are observable in logs or metrics.

## Tasks / Subtasks

- [x] Implement configuration model for edge cases (AC: 1, 2, 4)
  - [x] Extend generator config schema (for example `config/generator.yaml` and `GeneratorConfig` dataclass) with explicit fields for each edge-case toggle/rate using snake_case names.
  - [x] Add validation rules for impossible/invalid combinations (for example negative rates, rates > 1.0, or conflicting flags).
  - [x] Cover config validation with unit tests in `tests/generator/`.

- [x] Implement edge-case generation logic (AC: 1, 2, 5)
  - [x] Implement late and out-of-order events by delaying or re-ordering a subset of events based on configuration.
  - [x] Implement duplicates by emitting repeated events with the same IDs but clearly documented distinguishing fields if needed (for example duplicate reason).
  - [x] Implement missing steps by dropping or collapsing specific lifecycle events in an order flow according to configuration.
  - [x] Implement impossible durations by manipulating timestamps to violate normal ranges while still conforming to schema types.
  - [x] Implement courier offline behavior by changing courier status and potentially affecting in-flight orders.

- [x] Encode and document edge cases for JSON and AVRO (AC: 2, 3, 5)
  - [x] Ensure all edge-case behaviors are representable in both JSON and AVRO formats without changing schema structure between formats.
  - [x] Update or create sample outputs showing each edge case for both feeds.
  - [x] Update design note and PRD cross-references to document the encoding choices.

- [x] Integrate with debug and sample modes (AC: 1, 4)
  - [x] Ensure sample mode can produce small, edge-case-rich batches when desired.
  - [x] Ensure debug mode can reliably reproduce specific scenarios by combining edge-case configuration with throughput/entity caps.

- [x] Testing and observability hooks (AC: 1, 2, 3, 4, 5)
  - [x] Add structured logging or counters that surface how many events of each edge-case type were produced in a run.
  - [x] Add minimal tests to confirm that enabling a given edge-case flag actually changes the event stream in the expected way.

## Dev Notes

- Edge-case behavior configuration must align with the FRs in the PRD (especially FR5, FR32–FR35) and with the acceptance criteria in Epic 1 Story 1.3.
- Use the architecture document’s naming and structure conventions:
  - Keep generator code under a dedicated `generator/` package (for example within the `stream_analytics` package).
  - Maintain snake_case names for all configuration keys, event fields, and JSON payloads (`late_event_rate`, `courier_offline_rate`, `is_edge_case`, etc.).
  - Use `window_start` and `window_end` consistently in any time-windowed outputs derived from edge-case data.
- Edge cases should be intentional and explainable, not arbitrary chaos:
  - Late/out-of-order events must still be consistent with the event-time semantics and watermarks described in the PRD and architecture.
  - Duplicate and missing-step patterns should be recognizable later by Spark jobs and dashboards, allowing teaching of streaming correctness.
- Align generator behavior with the architecture’s observability guidance:
  - Emit structured logs for edge cases using the shared logging shape (timestamp, component, level, message, details, reason_code, etc.).
  - Make it easy for the dashboard’s Debug/Status page to surface whether a run is using edge-case-heavy configs.

### Project Structure Notes

- Keep configuration in a central `config/generator.yaml` (or equivalent) and load it via a shared config loader, rather than hardcoding edge-case parameters in multiple modules.
- Ensure generator modules are organized according to the architecture document (for example `generator/config_models.py`, `generator/edge_cases.py`, `generator/serialization.py`) and that tests are mirrored under `tests/generator/`.
- Any new datasets, columns, or JSON fields introduced to support edge cases must follow the naming and schema conventions defined in the architecture document and PRD, and be reflected in relevant docs (`design_note.md`, `demo_runbook.md`).

### References

- PRD: `_bmad-output/planning-artifacts/prd.md` (edge-case requirements, debug mode, NFRs).
- Epics & stories: `_bmad-output/planning-artifacts/epics.md` (Epic 1, Story 1.3).
- Architecture: `_bmad-output/planning-artifacts/architecture.md` (naming, structure, logging, and project structure conventions).

## Dev Agent Record

### Agent Model Used

Cursor Dev Agent – GPT-5.1 (2026-03-03)

### Debug Log References

- Generator edge-case logs (structured JSON), including counts by edge-case type and any schema validation issues.

### Completion Notes List

- Story file created with detailed acceptance criteria and implementation tasks for edge-case configuration.
- Aligned with PRD FR5, FR32–FR35 and Epic 1 Story 1.3; ready for downstream validation and implementation.
- Implemented edge-case configuration model (rates and validation) in `GeneratorConfig` and `config/generator.yaml`, with unit tests covering defaults, invalid values, and impossible combinations.
- Implemented edge-case generation logic in the sample generator path, including late events, duplicates, missing steps, impossible durations, and courier offline behavior driven by the new configuration fields, with tests to confirm that non-zero rates influence the generated streams.
- Documented JSON/AVRO encodings for all edge cases in `docs/design_note.md` and wired generator sample mode so that edge-case-rich batches can be produced and inspected for teaching and debugging.
- Added a debug-mode sample path (`--debug-sample` and `--debug-seed`) that clamps entity counts to `debug_mode_max_entity_count` and seeds the generator, enabling reproducible debug runs for teaching/demo scenarios.

### File List

- `_bmad-output/implementation-artifacts/1-3-control-edge-case-behaviors-via-configuration.md`
- `stream_analytics/generator/config_models.py`
- `tests/generator/test_config_models.py`
- `config/generator.yaml`
- `stream_analytics/generator/base_generators.py`
- `tests/generator/test_serialization_and_two_feeds.py`
 - `stream_analytics/generator/cli.py`
 - `stream_analytics/generator/entities.py`
 - `docs/design_note.md`
 - `_bmad-output/implementation-artifacts/sprint-status.yaml`
