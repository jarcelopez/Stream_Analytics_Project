# Story 6.1: document-implemented-use-cases-and-dashboard-views

Status: done

## Story

As a Student/Developer,  
I want documentation that explains the implemented basic, intermediate, and advanced analytics use cases and how they appear in the dashboard,  
so that graders can map rubric items directly to the running system.

## Acceptance Criteria

1. Given the final dashboard and metrics are implemented, when I review the use-case documentation, then it clearly identifies which dashboard pages, KPIs, and charts correspond to the required basic, intermediate, and advanced use cases in the PRD.
2. Given a grader is reading the documentation, when they follow references from each use case to the UI, then they can quickly find and observe the corresponding behavior in the running dashboard.

## Tasks / Subtasks

- [x] Inventory implemented analytics use cases and map each to PRD tiers (AC: 1)
  - [x] Confirm and document one Basic use case (windowed KPI) tied to concrete metrics.
  - [x] Confirm and document one Intermediate use case (stateful/session-like behavior) tied to concrete dashboard evidence.
  - [x] Confirm and document one Advanced use case (anomaly/stress metric) tied to concrete dashboard evidence.
- [x] Produce grader-facing dashboard mapping documentation (AC: 1, 2)
  - [x] Add or update a dedicated section in `README.md` and/or `docs/` that maps use-case tier -> dashboard page -> metric/chart -> expected behavior.
  - [x] Keep navigation language aligned with current Streamlit page names and controls.
  - [x] Include explicit "where to click" and "what to observe" guidance for each use case.
- [x] Add traceability references from use cases to implementation artifacts (AC: 2)
  - [x] Reference metric dataset fields and upstream Spark job outputs that power each dashboard view.
  - [x] Reference relevant status/debug indicators where they help graders validate live behavior.
  - [x] Ensure references are consistent with current repository paths and naming conventions.
- [x] Validate clarity and reproducibility of documentation flow (AC: 2)
  - [x] Run a documentation walkthrough from a grader perspective and confirm each mapped behavior can be located quickly.
  - [x] Ensure wording is concise, rubric-oriented, and avoids implementation ambiguity.

## Dev Notes

### Story Foundation and Business Context

- Story 6.1 directly implements `FR38`: document implemented Basic, Intermediate, and Advanced use cases and show how they appear in the dashboard.
- The primary outcome is grader efficiency and traceability: each rubric-relevant use case should map to concrete dashboard behavior and data sources.
- This story is documentation-first and must reflect real implemented behavior rather than aspirational architecture.

### Epic and Cross-Story Context

- Epic 6 closes the milestone with documentation/reflection artifacts after functional implementation is complete.
- Prior relevant completed stories:
  - Story 3.4 established windowed KPI + advanced anomaly/stress metrics and denormalized output dataset.
  - Story 4.1 established core KPI/time-series dashboard view.
  - Story 4.2 established zone/restaurant/time-window filtering and active-filter semantics.
  - Story 4.3 established health/anomaly-focused dashboard view.
  - Story 5.2 established debug/status visibility (useful for "live behavior" evidence).
- There is no previous story in Epic 6 (`story_num=1`), so cross-epic continuity is the main context source.

### Technical Requirements

- Documentation must explicitly map each use-case tier to:
  - dashboard page/view
  - KPI/chart elements
  - expected observable behavior in a running demo
  - data source or metric field backing the behavior
- Keep terminology consistent with PRD and architecture:
  - Basic: windowed KPI behavior
  - Intermediate: stateful/session-like or history-aware metric behavior
  - Advanced: anomaly/stress behavior with late-data-aware processing context
- Use concrete, scannable mapping tables or bullet lists rather than narrative-only prose.
- Ensure all field names, dataset names, and paths remain snake_case and match implemented artifacts.

### Architecture Compliance

- Respect architecture boundaries and data contracts documented in `architecture.md`:
  - Dashboard reads aggregated Parquet outputs and status artifacts; it is not the source of metric computation.
  - Spark jobs own metric production and event-time/watermark semantics.
  - Status artifacts (`status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`) are owned by orchestration/process components.
- Keep mappings aligned with expected structures:
  - Aggregated analytics surface: denormalized metrics dataset keyed by `zone_id`, `restaurant_id`, `window_start`, `window_end`.
  - Dashboard pages: Overview, Health/Anomalies, Debug/Status.

### Library and Framework Requirements (latest checked)

- Streamlit stable line: `1.56.x` (latest found: `1.56.0`); documentation should reference current page/interaction patterns and avoid deprecated guidance.
- Azure Event Hubs Python SDK: `azure-eventhub 5.15.1` stable line for ingestion/publish references.
- Structured Streaming watermark guidance (Databricks docs updated 2026-02): watermark configuration is mandatory/strongly recommended for stateful operations to avoid unbounded state and latency regressions.

### File Structure Requirements

- Primary files likely touched:
  - `README.md`
  - `docs/` documentation files for use-case mapping (for example runbook/design/evidence docs)
  - this story file for planning/traceability
- Do not create duplicate documentation surfaces with conflicting instructions; prefer extending existing canonical docs.
- Keep references consistent with existing package boundaries:
  - `stream_analytics/spark_jobs/`
  - `stream_analytics/dashboard/`
  - `stream_analytics/orchestration/`
  - `status/`, `logs/`, and output datasets

### Testing Requirements

- Run a documentation validation pass to confirm mapped paths/files/sections exist.
- If project has docs-oriented tests, run the relevant subset after updates.
- Perform one manual walkthrough in the running dashboard flow:
  - locate each mapped use case,
  - verify referenced page/control exists,
  - verify expected observable outcome language is accurate.

### Anti-Patterns to Avoid

- Do not describe use cases in abstract terms without concrete UI mapping.
- Do not invent new metrics/pages that are not implemented.
- Do not drift from established naming/status conventions.
- Do not duplicate architecture decisions in contradictory form.
- Do not bury critical rubric mappings in long paragraphs; keep them discoverable.

### Latest Technical Information

- Streamlit `1.56.0` is current stable and supports modern navigation/container behavior relevant to clear dashboard documentation.
- Event Hubs Python SDK `5.15.1` remains current stable and should be the default reference line for producer/consumer docs.
- Current watermark best-practice references emphasize explicit event-time watermarks for stateful/windowed logic and careful late-data thresholds.

### Project Context Reference

- No `project-context.md` file was discovered; context sourced from planning artifacts and prior implementation stories.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 6 Story 6.1 definition; cross-story context from Epics 3-5)
- `_bmad-output/planning-artifacts/prd.md` (`FR38`, dashboard/use-case expectations, NFR implications)
- `_bmad-output/planning-artifacts/architecture.md` (dashboard/spark boundaries, naming conventions, status/data contracts)
- [Streamlit 1.56.0 release](https://github.com/streamlit/streamlit/releases/tag/1.56.0)
- [Azure Event Hubs Python SDK overview](https://learn.microsoft.com/en-us/python/api/overview/azure/event-hubs?view=azure-python)
- [Structured Streaming watermarks guidance](https://learn.microsoft.com/en-us/azure/databricks/structured-streaming/watermarks)

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- Story context generated from planning and architecture artifacts with story key `6-1-document-implemented-use-cases-and-dashboard-views`.
- Sprint status aligned for review completion tracking on story key `6-1-document-implemented-use-cases-and-dashboard-views`.
- Reviewed implemented dashboard surface in `stream_analytics/dashboard/app.py` to anchor page names, controls, and observable behavior.
- Confirmed metric lineage from `stream_analytics/spark_jobs/windowed_kpis.py` and `stream_analytics/spark_jobs/anomaly_scores.py` for traceable documentation references.
- Executed validation tests: `python -m pytest tests/docs/test_demo_runbook_docs.py tests/dashboard/test_overview_kpis.py tests/dashboard/test_health_anomalies.py tests/dashboard/test_status_display.py` (23 passed).

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story prepared as a documentation-first implementation with strict rubric-to-UI traceability requirements.
- Cross-epic dependencies and architecture constraints captured to prevent drift from implemented system behavior.
- Latest technology references added to reduce outdated implementation/documentation patterns.
- Added a dedicated README mapping section that links Basic/Intermediate/Advanced use cases to concrete dashboard pages, controls, metrics, and expected observations.
- Added explicit grader walk-through steps with "where to click" and "what to observe" guidance for reproducible validation.
- Added traceability references to curated metrics fields, upstream Spark job outputs, and live status indicators (`RUNNING`, `last_batch_ts`, batch age).

### File List

- `_bmad-output/implementation-artifacts/6-1-document-implemented-use-cases-and-dashboard-views.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `README.md`

### Change Log

- 2026-04-15: Documented rubric-tier use-case mapping in `README.md` with concrete dashboard navigation, observable behavior, and metric lineage references.
- 2026-04-15: Completed Story 6.1 task checklist and updated Dev Agent Record/File List for review readiness.
- 2026-04-15: Applied code-review fixes to clarify Intermediate vs Advanced mapping evidence and adjusted grader walk-through start conditions.

## Senior Developer Review (AI)

### Reviewer

Javi

### Date

2026-04-15

### Outcome

Approved after fixes.

### Findings and Resolutions

- HIGH: Intermediate use-case mapping was not clearly distinct from Advanced mapping in `README.md`.
  - Resolution: Intermediate mapping now requires a two-page verification flow (`Overview` + `Health/Anomalies`) with fixed-threshold, cross-window comparison criteria.
- MEDIUM: Validation wording incorrectly implied `severity_source` proved stateful behavior.
  - Resolution: Validation signal now uses observable cross-window ranking changes under fixed threshold/top-N instead of `severity_source`.
- MEDIUM: Grader walk-through assumed unconditional `Start Demo` click.
  - Resolution: Walk-through now instructs graders to click `Start Demo` only when `Spark Streaming` is not already `RUNNING`.
- LOW: Debug log text referenced stale sprint-state wording.
  - Resolution: Updated Dev Agent debug note to use current review-completion alignment wording.
