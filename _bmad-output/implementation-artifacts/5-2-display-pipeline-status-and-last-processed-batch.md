# Story 5.2: display-pipeline-status-and-last-processed-batch

Status: done

## Story

As a Student/Developer,  
I want the dashboard to show generator and streaming-job status and the timestamp of the last processed batch,  
so that I can quickly tell if the demo is healthy.

## Acceptance Criteria

1. Given the demo has been started, when I open the debug/status page in the dashboard, then I see status indicators for generator and streaming jobs (for example RUNNING/STOPPED/ERROR) and a timestamp for the last successfully processed batch.
2. Given the demo is healthy and new data is flowing, when I wait at least the documented refresh interval (for example 10 seconds), then the last-batch timestamp updates to reflect recent processing activity.

## Tasks / Subtasks

- [x] Extend debug/status dashboard view to surface live pipeline status (AC: 1)
  - [x] Update `stream_analytics/dashboard/app.py` (or `stream_analytics/dashboard/debug_status_page.py` if split) to render generator and Spark status blocks using status artifact readers.
  - [x] Show explicit state badges for `RUNNING`, `STOPPED`, `ERROR` and include fallback message for stale/missing status files.
  - [x] Preserve existing demo lifecycle controls and avoid regressions in Start/Stop/Reset behavior from Story 5.1.
- [x] Implement and wire last processed batch timestamp display (AC: 1,2)
  - [x] Read `last_batch_ts` from Spark status artifact and render as UTC plus local-readable format.
  - [x] Add "last updated" age indicator (for example seconds since batch) to quickly detect stalled pipelines.
  - [x] Ensure dashboard refresh cadence updates the timestamp view at least every 10 seconds while demo is running.
- [x] Harden status artifact contract and update flows (AC: 1,2)
  - [x] Confirm `stream_analytics/orchestration/status_files.py` always writes required keys: `status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`, `message`.
  - [x] Ensure status writer path is deterministic (`status/generator_status.json`, `status/spark_job_status.json`) and resilient to missing files.
  - [x] Enforce safe defaults when `last_batch_ts` is null/empty (display as waiting/no batch yet, not as crash).
- [x] Propagate batch progress from orchestration/runtime hooks (AC: 2)
  - [x] Update `stream_analytics/orchestration/demo_runner.py` to refresh Spark status heartbeat and `last_batch_ts` when new processing checkpoints are observed.
  - [x] If real batch timestamps are unavailable from Spark process output, implement a documented approximation path and mark it clearly in status `message`.
  - [x] Avoid blocking Streamlit render loop; collect status updates through lightweight polling/readers.
- [x] Add tests for status rendering and timestamp update behavior (AC: 1,2)
  - [x] Add/extend tests in `tests/dashboard/test_demo_controls.py` and `tests/dashboard/test_status_display.py` for status badge visibility, missing-file fallback, and timestamp rendering.
  - [x] Add orchestration tests in `tests/orchestration/test_demo_runner.py` for `last_batch_ts` update semantics and stale-state transitions.
  - [x] Include regression coverage to verify Story 5.1 controls remain idempotent and stable.
- [x] Update docs for operator clarity (supports Epic 5 continuity)
  - [x] Update `README.md` demo section to explain status panel fields and expected update cadence.
  - [x] Add troubleshooting notes for stale `last_batch_ts` and recovery checks (Spark running but no recent batch).

## Dev Notes

### Story Foundation and Business Context

- Story 5.2 implements `FR30` from Epic 5 by making pipeline health observable from the dashboard without terminal inspection.
- This is the monitoring complement to Story 5.1 control-plane actions; controls must remain stable while adding richer telemetry.

### Epic and Cross-Story Context

- Story 5.1 already introduced control actions and status artifacts. Reuse those contracts instead of introducing parallel status sources.
- Story 5.3 documentation depends on accurate status semantics and reproducible health checks defined in this story.
- Keep public UI semantics stable (`RUNNING`/`STOPPED`/`ERROR`, `last_batch_ts`) so downstream docs and grading scripts do not drift.

### Previous Story Intelligence (5.1 learnings to carry forward)

- Preserve idempotent orchestration behavior and mixed-state hardening already added in Story 5.1.
- Keep errors actionable in UI; do not surface raw exceptions where operator guidance is expected.
- Avoid claiming implementation completion in story records unless backed by tests and touched-file list.
- Startup failure cleanup patterns (partial launch rollback, PID/status cleanup) must remain intact.

### Technical Requirements

- Read status from `status/generator_status.json` and `status/spark_job_status.json` through shared utility functions only.
- Maintain structured JSON schema and snake_case keys across generator, orchestration, and dashboard.
- Treat `last_batch_ts` as authoritative when present; when absent, render a clear non-error waiting state.
- Keep refresh strategy lightweight and deterministic; target at least every 10 seconds while run state is `RUNNING`.
- Preserve compatibility with Windows execution paths and existing process management in orchestration.

### Architecture Compliance

- Respect architecture boundaries:
  - Dashboard: presentation + control trigger only.
  - Orchestration: process lifecycle and status writes.
  - Spark/generator: producers of telemetry signals.
- Keep contracts aligned with architecture conventions:
  - `status`: `RUNNING`/`STOPPED`/`ERROR`
  - `last_heartbeat_ts`, `last_batch_ts`, `debug_mode` in ISO-8601 UTC
- Reuse `stream_analytics/common/` utilities and existing status helpers; no duplicate readers/writers.

### Library and Framework Requirements (latest checked)

- Streamlit: use stable `1.56.x` line (latest `1.56.0`) and avoid deprecated experimental state APIs for page rerun/control flows.
- PySpark: keep runtime assumptions compatible with stable `4.1.1` unless course environment pins otherwise.
- Azure Event Hubs SDK: maintain compatibility with `azure-eventhub` `5.x` (latest `5.15.1`) and avoid new code paths that depend on deprecated `uamqp_transport`.

### File Structure Requirements

- Primary files expected to modify:
  - `stream_analytics/dashboard/app.py` or `stream_analytics/dashboard/debug_status_page.py`
  - `stream_analytics/orchestration/status_files.py`
  - `stream_analytics/orchestration/demo_runner.py`
  - `config/dashboard.yaml` (if refresh cadence/status path config needs expansion)
  - `README.md`
- Primary test files expected to modify/add:
  - `tests/dashboard/test_demo_controls.py`
  - `tests/dashboard/test_status_display.py`
  - `tests/orchestration/test_demo_runner.py`

### Testing Requirements

- Dashboard tests must verify:
  - status badges render correctly for each state,
  - missing/corrupt status files render actionable fallback,
  - `last_batch_ts` displays and refreshes with expected cadence.
- Orchestration tests must verify:
  - status updates keep required schema keys,
  - `last_batch_ts` transitions from null to recent timestamp during healthy runs,
  - stale heartbeat/batch behavior surfaces non-crashing degraded state.
- Regression tests must confirm Story 5.1 lifecycle controls remain idempotent and no duplicate process spawns occur.

### Anti-Patterns to Avoid

- Do not parse process stdout in Streamlit page render directly.
- Do not make dashboard status depend on ad-hoc global variables instead of status artifacts.
- Do not mark stale `last_batch_ts` as `ERROR` automatically without corroborating process status.
- Do not hardcode local absolute paths in UI/orchestration code.

### Git Intelligence Summary

- Recent commits show established pattern of updating:
  - dashboard UI module(s),
  - orchestration status/process helpers,
  - config and README,
  - focused dashboard/orchestration tests.
- Continue this footprint for Story 5.2 to remain consistent with repo conventions and review expectations.

### Latest Technical Information

- Streamlit `1.56.0` adds stable navigation/widget improvements; existing dashboard controls should remain on non-experimental APIs.
- PySpark `4.1.1` is current stable on PyPI; 4.2.x is pre-release and should not be a default target for this story.
- Azure Event Hubs `5.15.1` remains the current stable Python SDK; pyAMQP is the preferred transport path.

### Project Context Reference

- No `project-context.md` file was discovered in the repository; context is sourced from `epics.md`, `prd.md`, `architecture.md`, `sprint-status.yaml`, and prior implementation artifacts.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 5, Story 5.2 and dependencies)
- `_bmad-output/planning-artifacts/prd.md` (`FR30`, `FR31`, `NFR1`, `NFR2`, `NFR5`, `NFR6`)
- `_bmad-output/planning-artifacts/architecture.md` (status artifact contracts, component boundaries, dashboard debug/status expectations)
- `_bmad-output/implementation-artifacts/5-1-start-and-stop-demo-from-the-dashboard.md` (control-plane foundation, review corrections)
- [Streamlit 1.56.0 release](https://github.com/streamlit/streamlit/releases/tag/1.56.0)
- [PySpark on PyPI](https://pypi.org/project/pyspark/)
- [Azure Event Hubs SDK for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/event-hubs?view=azure-python)

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- `pytest tests/dashboard/test_demo_controls.py tests/dashboard/test_status_display.py tests/orchestration/test_demo_runner.py`
- `pytest`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story marked ready-for-dev with architecture and repo-pattern guardrails.
- Previous-story learnings and code-review fixes from Story 5.1 were incorporated to reduce repeated failures.
- Technical version guidance refreshed for Streamlit, PySpark, and Azure Event Hubs SDK.
- Added a dedicated dashboard "Pipeline Status" section with generator and Spark state badges, resilient status messages, and last processed batch visibility.
- Implemented batch timestamp rendering as UTC plus local-readable time and a batch age indicator for stalled-flow detection.
- Added orchestration heartbeat refresh behavior for RUNNING status files; when real batch timestamps are unavailable, `last_batch_ts` is approximated and explicitly documented in status `message`.
- Added status-focused tests for dashboard display helpers, status-file fallback behavior, and `read_demo_status` batch-timestamp propagation semantics.
- Full regression suite passes: 99 tests total.

### File List

- `_bmad-output/implementation-artifacts/5-2-display-pipeline-status-and-last-processed-batch.md`
- `stream_analytics/dashboard/app.py`
- `stream_analytics/orchestration/demo_runner.py`
- `tests/dashboard/test_demo_controls.py`
- `tests/dashboard/test_status_display.py`
- `tests/orchestration/test_demo_runner.py`
- `README.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Senior Developer Review (AI)

- 2026-04-15: Fixed code-review findings by adding an explicit `Debug/Status` dashboard page option, making heartbeat-approximation mode refresh `last_batch_ts` continuously while `RUNNING`, and extending orchestration tests to verify cadence-based timestamp updates.
- 2026-04-15: Verified story/gitreality alignment by documenting sprint tracking file updates in this story's File List.

## Change Log

- 2026-04-15: Implemented Story 5.2 pipeline status panel, last-batch telemetry display, orchestration heartbeat approximation path, and test/doc updates.
- 2026-04-15: Applied code-review fixes for AC2 timestamp refresh semantics, debug/status page discoverability, and story file-list traceability.
