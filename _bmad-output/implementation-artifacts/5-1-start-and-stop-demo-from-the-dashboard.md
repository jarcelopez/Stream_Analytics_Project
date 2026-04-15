# Story 5.1: start-and-stop-demo-from-the-dashboard

Status: done

## Story

As a Student/Developer,  
I want to start and stop a full demo run from the Streamlit UI,  
so that I do not have to juggle multiple CLI processes manually.

## Acceptance Criteria

1. Given the environment is configured and the necessary scripts are available, when I click the "Start Demo" control in the UI, then the generator and required Spark jobs are started (directly or via orchestration helpers) and the dashboard indicates that the demo is running.
2. Given a demo run is in progress, when I click the "Stop Demo" or "Reset Demo" control, then the associated processes are cleanly stopped or reset according to the documentation, without leaving orphaned jobs.

## Tasks / Subtasks

- [x] Add dashboard controls for demo lifecycle management (AC: 1,2)
  - [x] Extend `stream_analytics/dashboard/app.py` with explicit controls for `Start Demo`, `Stop Demo`, and `Reset Demo`.
  - [x] Keep existing `Overview` and `Health/Anomalies` behavior stable; avoid regressions in KPI/filter rendering.
  - [x] Render clear run-state messaging in the UI (`RUNNING`, `STOPPED`, `ERROR`) tied to orchestration status artifacts.
- [x] Implement orchestration module for process lifecycle (AC: 1,2)
  - [x] Create `stream_analytics/orchestration/demo_runner.py` to start and stop generator and Spark jobs via controlled subprocess calls.
  - [x] Ensure start operation is idempotent (do not spawn duplicates if already running).
  - [x] Ensure stop/reset operation terminates child processes cleanly on Windows and avoids orphaned processes.
- [x] Add status artifact contract and utilities (AC: 1,2)
  - [x] Create `stream_analytics/orchestration/status_files.py` to write/read status JSON files (generator and spark).
  - [x] Persist and update required keys: `status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`, `message`.
  - [x] Store artifacts under a single predictable location (for example `status/`) and keep schema stable.
- [x] Add configuration and command wiring (AC: 1,2)
  - [x] Extend `config/dashboard.yaml` and/or `config/spark_jobs.yaml` with orchestration command paths/args and status paths.
  - [x] Keep command execution configurable; do not hardcode machine-specific paths.
  - [x] Add guardrails for missing config (surface actionable error in UI instead of tracebacks).
- [x] Add automated tests for orchestration and UI integration (AC: 1,2)
  - [x] Add unit tests for start/stop/reset behavior, idempotency, and status updates under `tests/dashboard/` and/or `tests/orchestration/`.
  - [x] Add tests for dashboard control state, including disabled/enabled behavior and run-state messages.
  - [x] Add regression tests confirming existing dashboard pages remain functional when orchestration controls are introduced.
- [x] Update docs for reproducible local usage (supports Epic 5 continuity)
  - [x] Document start/stop/reset behavior and expected status artifacts in `README.md` (or dedicated runbook).
  - [x] Include troubleshooting notes for stale PID/status files and manual recovery path.

## Dev Notes

### Story Foundation and Business Context

- Epic 5 is focused on orchestrated demo operations from UI; Story 5.1 delivers the control-plane foundation for `FR28` and `FR29`.
- This story should establish reliable lifecycle controls first; richer status telemetry is covered in Story 5.2.

### Epic and Cross-Story Context

- Story 5.2 depends on Story 5.1 control semantics and status artifact shape to display health and last processed batch.
- Story 5.3 documentation quality depends on a deterministic and reproducible start/stop/reset flow created here.
- Keep interfaces stable now to avoid rework across all remaining Epic 5 stories.

### Technical Requirements

- Preserve current dashboard architecture in `stream_analytics/dashboard/app.py`, adding control widgets without breaking existing page and filter logic.
- Introduce orchestration code in a dedicated package (`stream_analytics/orchestration/`) rather than embedding subprocess logic in UI rendering code.
- Use structured status artifacts in JSON with snake_case keys and UTC ISO-8601 timestamps.
- Implement process handling with explicit PID tracking and safe termination flow; fail fast on invalid commands and report actionable error messages in UI.
- Ensure operations are idempotent:
  - Start while running must not duplicate child processes.
  - Stop/reset while already stopped must return a clean no-op success state.

### Architecture Compliance

- Respect component boundaries from architecture:
  - Dashboard remains the presentation and control trigger.
  - Orchestration module owns process invocation and status-file writes.
  - Spark/generator components remain independent workers.
- Reuse shared configuration and logging patterns from `stream_analytics/common/` where possible.
- Maintain naming conventions and structured logging standards used in previous stories.

### Library and Framework Requirements

- Streamlit:
  - Keep compatibility with stable `1.56.x` behavior for widgets and rerun flow.
  - Avoid deprecated experimental APIs for state/control flows.
- Azure Event Hubs Python SDK:
  - Use `azure-eventhub` `5.x` line (latest stable: `5.15.1`) for any touch points in orchestration or validation hooks.
- PySpark:
  - Keep job invocation assumptions compatible with currently documented stable line (`pyspark 4.1.1`, Python >=3.10), unless course environment pins a lower supported runtime.

### File Structure Requirements

- Expected files to modify:
  - `stream_analytics/dashboard/app.py`
  - `config/dashboard.yaml`
  - `README.md` (or demo runbook if present)
- Expected files to add:
  - `stream_analytics/orchestration/__init__.py`
  - `stream_analytics/orchestration/demo_runner.py`
  - `stream_analytics/orchestration/status_files.py`
  - `tests/orchestration/test_demo_runner.py` (or equivalent coverage in existing dashboard tests)
- Optional helper scripts (only if needed and configurable):
  - `scripts/run_demo_local.ps1` or `scripts/run_demo_local.sh`

### Testing Requirements

- Unit-test `demo_runner` for:
  - start success path,
  - stop/reset success path,
  - idempotent repeated calls,
  - command failure propagation with friendly error text.
- Unit-test status utility for:
  - schema shape and required keys,
  - timestamp formatting and update behavior,
  - missing/corrupt file recovery.
- Dashboard tests must verify:
  - controls are visible and actionable,
  - status state is displayed correctly,
  - existing overview/health rendering remains unchanged.
- Run full test suite after implementation and include focused orchestration test output in completion notes.

### Anti-Patterns to Avoid

- Do not invoke long-running jobs directly inside Streamlit render loops without process guards.
- Do not hardcode absolute local paths, shell-specific commands, or credentials in code.
- Do not let status files become the single source of truth for process existence without PID/process checks.
- Do not silently swallow process-launch errors; surface clear operator guidance in UI.
- Do not alter existing KPI/anomaly logic while implementing lifecycle controls.

### Project Context Reference

- No `project-context.md` file was discovered in the repository; context is sourced from `epics.md`, `prd.md`, `architecture.md`, sprint status, and existing implementation artifacts.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 5, Story 5.1, dependencies on 5.2 and 5.3)
- `_bmad-output/planning-artifacts/prd.md` (`FR28`, `FR29`, `FR30`, `FR31`, `NFR5`, `NFR6`)
- `_bmad-output/planning-artifacts/architecture.md` (orchestration model, status artifact conventions, component boundaries)
- `_bmad-output/implementation-artifacts/4-3-add-health-and-anomaly-view.md` (dashboard structure and regression expectations)
- [Streamlit release 1.56.0](https://github.com/streamlit/streamlit/releases/tag/1.56.0)
- [PySpark 4.1.1 package metadata](https://pypi.org/project/pyspark/)
- [Azure Event Hubs SDK for Python (v5)](https://learn.microsoft.com/en-us/python/api/overview/azure/event-hubs?view=azure-python)

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- N/A (story creation workflow output)

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story marked ready for development with architecture-aligned implementation guardrails.
- Epic 5 cross-story dependencies captured to reduce rework in Stories 5.2 and 5.3.
- Current repo reality captured: dashboard exists, orchestration package not yet implemented.
- Latest framework/library context captured for Streamlit, PySpark, and Azure Event Hubs.
- Added dashboard lifecycle controls (`Start Demo`, `Stop Demo`, `Reset Demo`) with run-state messaging and disabled/enabled behavior tied to orchestration status.
- Added orchestration lifecycle and status modules with JSON status contract and PID-based process handling for idempotent start/stop/reset.
- Added configurable orchestration command/status settings to `config/dashboard.yaml` with actionable guardrails for missing commands.
- Added orchestration and dashboard control tests; all related dashboard/orchestration tests pass locally.
- Updated README with Story 5.1 runbook details and troubleshooting for stale PID/status artifacts.

### File List

- `_bmad-output/implementation-artifacts/5-1-start-and-stop-demo-from-the-dashboard.md`
- `stream_analytics/dashboard/app.py`
- `stream_analytics/orchestration/__init__.py`
- `stream_analytics/orchestration/demo_runner.py`
- `stream_analytics/orchestration/status_files.py`
- `config/dashboard.yaml`
- `tests/orchestration/test_demo_runner.py`
- `tests/dashboard/test_demo_controls.py`
- `README.md`

## Change Log

- 2026-04-15: Implemented Story 5.1 dashboard demo lifecycle controls, orchestration status/process management, configurable command wiring, and test/documentation updates. All tests passing (`pytest`).
- 2026-04-15: Code review fixes applied for Story 5.1: startup failure cleanup, mixed-process run-state hardening, and UI guardrails for actionable control errors.

## Senior Developer Review (AI)

### Reviewer

Javi

### Date

2026-04-15

### Outcome

Changes Requested -> Fixed

### Findings Addressed

- Fixed orphan-process risk during partial startup failure by terminating already spawned generator process and cleaning PID files in `start_demo`.
- Fixed mixed-state reporting (`RUNNING` + `STOPPED`) to avoid false `STOPPED` state and prevent duplicate starts.
- Added UI-level guardrail in dashboard controls to surface actionable orchestration errors instead of unhandled exceptions.
- Added orchestration regression test to verify cleanup when Spark startup fails after generator launch.
- Corrected story File List to focus on implementation files and exclude sprint tracking artifact from implementation claims.

