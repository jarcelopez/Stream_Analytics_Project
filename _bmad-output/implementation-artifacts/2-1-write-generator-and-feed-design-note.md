% Story header and core user story for Epic 2, Story 1
# Story 2.1: Write Generator and Feed Design Note

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,
I want to maintain a design note that describes the two feeds, their schemas, and key assumptions,
so that graders and collaborators can understand how the data supports the planned analytics.

## Acceptance Criteria

1. Given the current generator implementation and AVRO/JSON schemas, when I update the design note, then it clearly describes each feed’s purpose, core entities and IDs, event‑time fields, and how the data enables the Milestone 2 analytics (windows, joins, anomaly metrics).
2. Given edge‑case behaviors are supported in the generator, when I review the design note, then it explicitly documents which edge cases exist (late, duplicate, missing‑step, impossible‑duration, courier‑offline) and how they are encoded in the events.
3. Given the PRD and architecture documents, when a grader reads the design note, then they can trace requirements FR1–FR6, FR32–FR33 and related architecture decisions back to specific schema fields and feed behaviors.
4. Given the design note is updated, when Milestone 2 work begins, then Spark job and dashboard implementers can rely on the design note as the single source of truth for feed semantics without needing to re‑infer intent from code.

## Tasks / Subtasks

- [x] Draft or update `docs/design_note.md` structure
  - [x] Add overview of both feeds (Order Events, Courier Status) and their roles in the pipeline
- [x] Document schemas and entities
  - [x] Describe core entities and IDs (`order_id`, `courier_id`, `restaurant_id`, `zone_id`)
  - [x] Document required fields, types, and any nullable/optional fields
  - [x] Call out event‑time fields and any additional timestamps
- [x] Capture edge‑case behaviors
  - [x] List all supported edge cases (late, duplicate, missing‑step, impossible‑duration, courier‑offline)
  - [x] Explain how each edge case is encoded in events (which fields, flag patterns, value ranges)
  - [x] Provide at least one concrete example per edge case (JSON and/or AVRO‑decoded)
- [x] Connect feeds to analytics and milestones
  - [x] Map feed fields to planned analytics (windows, joins, anomaly metrics, ZSI)
  - [x] Reference which PRD FRs and NFRs each part of the design supports
- [x] Review and polish
  - [x] Cross‑check design note against AVRO schemas and generator configuration
  - [x] Verify consistency with PRD and architecture documents
  - [x] Run spell/format check and commit design note alongside generator work

## Dev Notes

- The design note should live in `docs/design_note.md` as referenced in the architecture document and project structure.
- Treat AVRO schemas for order events and courier status as the contract between generator, Spark jobs, and dashboard; the design note must describe these contracts clearly, including any planned schema evolution.
- Align terminology and field names with the established naming conventions (snake_case for all fields/columns/JSON keys; `window_start` and `window_end` for time‑window columns; `event_time` for event timestamp).
- Ensure the design note explains how generator configuration options (entity counts, demand levels, edge‑case rates, debug/sample modes) shape the resulting data and support teaching/assessment scenarios.
- Use the design note to make streaming correctness intentional: describe how late/out‑of‑order, duplicates, missing steps, and impossible durations are produced so that later Spark jobs and dashboards can demonstrate correct handling.

### Project Structure Notes

- Place feed and schema documentation under `docs/design_note.md` and keep it in sync with:
  - `stream_analytics/generator/schemas/` (e.g. `order_events.avsc`, `courier_status.avsc`)
  - `stream_analytics/generator/config_models.py` and other generator config files
- Follow the agreed project layout from the architecture document (`generator/`, `spark_jobs/`, `dashboard/`, `orchestration/`, `common/`, `tests/`, `docs/`).
- When adding new fields or changing schemas, document the change and rationale in the design note, including any impact on analytics or downstream jobs.

### References

- PRD: `_bmad-output/planning-artifacts/prd.md` – see Functional Requirements FR1–FR6, FR32–FR33, and Documentation FR36–FR37.
- Epics & stories: `_bmad-output/planning-artifacts/epics.md` – see Epic 1 (generator behavior) and Epic 2, Story 2.1 (this story).
- Architecture: `_bmad-output/planning-artifacts/architecture.md` – see schema‑driven design, aggregated metrics model, and project structure.
- Future Milestone 2 work: metrics, anomaly scores, and Zone Stress Index that rely on the feed semantics defined in this design note.

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

- Generator behavior and schema issues should be visible in `logs/generator.log` (structured JSON lines with `component="generator"` and appropriate `reason_code`s).
- Any mismatches between design note, schemas, and actual events should be captured as ERROR/WARN entries with enough context to update the design note or code.

### Completion Notes List

- Use this section to record what was actually done when implementing this story (e.g. which sections of `docs/design_note.md` were added or revised, which schemas changed, which examples were captured).
- Updated `docs/design_note.md` with feed overviews, Milestone 2 analytics mapping (windows, joins, anomaly/ZSI), concrete JSON examples for all documented edge cases, and verified existing generator tests (`pytest`) pass without regressions.
- Refined `docs/design_note.md` after adversarial code review to make the JSON time representation match the actual generator implementation and tests (microsecond epoch integers shared with AVRO), explicitly call out this small deviation from the architecture doc, make FR1–FR6/FR32–FR33 and NFR mappings explicit, and add an AC/test mapping section for Story 2.1.

### File List

- `docs/design_note.md` (primary artifact for this story)
- `stream_analytics/generator/schemas/order_events.avsc` (referenced and explained)
- `stream_analytics/generator/schemas/courier_status.avsc` (referenced and explained)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated automatically by workflows to track story status)
- Any additional sample JSON/AVRO files or snippets referenced from the design note
