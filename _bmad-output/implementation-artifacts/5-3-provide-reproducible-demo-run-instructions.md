# Story 5.3: provide-reproducible-demo-run-instructions

Status: done

## Story

As a Professor/Grader,  
I want clear instructions for reproducing a typical demo run,  
so that I can evaluate the project without modifying code or guessing steps.

## Acceptance Criteria

1. Given I have access to the repo and environment prerequisites, when I follow the demo run instructions in the README or demo runbook, then I can start the demo, observe live metrics updating, and stop the demo without editing any source files.

## Tasks / Subtasks

- [x] Create a reproducible demo runbook flow in repository docs (AC: 1)
  - [x] Add/update a dedicated runbook section in `README.md` and `docs/demo_runbook.md` with exact command blocks for setup, start, monitor, and stop flows.
  - [x] Keep all commands copy-paste ready for Windows PowerShell and clearly label any Linux/macOS alternatives.
  - [x] Ensure documented flow uses existing UI controls and orchestration scripts introduced in Stories 5.1 and 5.2.
- [x] Document prerequisites and environment validation gates (AC: 1)
  - [x] Add prerequisites checklist: Python version, dependencies install step, Azure/Event Hubs config file or environment variables, and required local folders (`status/`, `logs/`, output paths).
  - [x] Add preflight validation commands so a grader can confirm setup before running the demo.
  - [x] Explicitly state that no source-code edits are required for the standard run.
- [x] Document end-to-end demo lifecycle with observable checkpoints (AC: 1)
  - [x] Define expected UI checkpoints after start (generator state, Spark state, `last_batch_ts` refresh cadence).
  - [x] Add "healthy demo" signals and "stalled/error" signals tied to the Debug/Status page semantics from Story 5.2.
  - [x] Provide a deterministic stop/reset path and post-run cleanup verification (no orphaned processes, status files in expected terminal state).
- [x] Add troubleshooting paths that preserve reproducibility (AC: 1)
  - [x] Add a concise troubleshooting table for common failures (missing Azure config, stale `last_batch_ts`, status file missing/corrupt, Spark not reachable).
  - [x] Document recovery commands and when to use `Reset Demo` versus full restart.
  - [x] Include expected log/status artifacts to inspect (`status/generator_status.json`, `status/spark_job_status.json`, `logs/*.log`).
- [x] Add or update tests/docs checks for story coverage (AC: 1)
  - [x] Add documentation validation coverage (for example, test that runbook paths and referenced scripts/files exist).
  - [x] Extend existing dashboard/orchestration tests only if docs reveal behavior mismatch needing code guardrails.
  - [x] Run the existing test suite subset tied to orchestration and status display to prevent regressions from any supporting code changes.

## Dev Notes

### Story Foundation and Business Context

- Story 5.3 implements `FR31` by making the demo operation reproducible for evaluators without any code edits.
- It operationalizes `NFR5` (setup/run in <=45 minutes for a fresh user) and supports evidence for `NFR6` (stable full demo path without unhandled failures).
- This story is documentation-first but tightly coupled to real behavior from Stories 5.1 (lifecycle controls) and 5.2 (status observability).

### Epic and Cross-Story Context

- Story 5.1 established Start/Stop/Reset orchestration behavior from the dashboard.
- Story 5.2 established Debug/Status semantics: `RUNNING`/`STOPPED`/`ERROR`, heartbeat, and `last_batch_ts`.
- Story 5.3 must reuse those existing contracts and naming conventions; it must not introduce alternate operator paths that conflict with current UI semantics.

### Previous Story Intelligence (from Story 5.2)

- Keep status guidance actionable and avoid exposing raw stack traces in user-facing run steps.
- Preserve idempotent start/stop/reset expectations; documentation should guide users toward controls that avoid duplicate process spawns.
- Treat stale batch timestamps as diagnosable degraded state, not immediate hard-failure, unless corroborated by status/error signals.
- Ensure all documented checks map to actual artifacts and test-covered code paths.

### Technical Requirements

- Demo instructions must be executable as written in the current repository state with no source modification.
- Commands, paths, and filenames must remain aligned with existing conventions and Windows-friendly execution (`powershell` first).
- Status/health checks in docs must reference artifact contracts from orchestration:
  - `status/generator_status.json`
  - `status/spark_job_status.json`
  - keys: `status`, `last_heartbeat_ts`, `last_batch_ts`, `debug_mode`, `message`
- Instructions must explicitly include expected refresh behavior (at least every ~10 seconds while running) for the batch timestamp/heartbeat panel.

### Architecture Compliance

- Respect architecture boundaries:
  - `dashboard/` is control + visualization layer.
  - `orchestration/` owns process lifecycle and status writes.
  - `spark_jobs/` and generator remain producers of telemetry/data.
- Keep naming and contract consistency (snake_case fields, status artifact paths, and standardized status values).
- Reuse established README + runbook documentation patterns rather than creating disconnected documentation surfaces.

### Library and Framework Requirements (latest checked)

- Streamlit stable line is `1.56.x` (latest `1.56.0`); instructions should avoid deprecated/experimental commands for standard operator flow.
- PySpark stable on PyPI is `4.1.1`; prefer stable docs and examples aligned with this version.
- Azure Event Hubs Python SDK stable is `azure-eventhub 5.15.1`; keep transport guidance aligned with current pyAMQP-based defaults.

### File Structure Requirements

- Primary files expected to modify:
  - `README.md`
  - `docs/demo_runbook.md`
  - optionally `docs/nfr_validation.md` (if runbook evidence links are added)
- Supporting files that may require alignment updates:
  - `config/dashboard.yaml` (only if documented cadence differs from current defaults)
  - `stream_analytics/orchestration/demo_runner.py` (only if runbook uncovers actual behavior mismatch)
  - `stream_analytics/dashboard/app.py` (only if UI labels/states in docs do not match real app output)
- Tests likely touched only when behavior/documentation drift is discovered:
  - `tests/dashboard/test_demo_controls.py`
  - `tests/dashboard/test_status_display.py`
  - `tests/orchestration/test_demo_runner.py`

### Testing Requirements

- Validate all documented commands and referenced files exist and run in expected order.
- Verify demo lifecycle path from documentation:
  - start from UI/control path,
  - monitor status updates and batch timestamp refresh,
  - stop/reset cleanly.
- Run targeted regressions:
  - `pytest tests/dashboard/test_demo_controls.py tests/dashboard/test_status_display.py tests/orchestration/test_demo_runner.py`
- If docs-only changes are made, still execute at least one smoke flow to ensure runbook fidelity.

### Anti-Patterns to Avoid

- Do not require graders to edit `.py` files, constants, or hardcoded paths.
- Do not introduce multiple "official" demo run paths with conflicting steps.
- Do not document stale/deprecated status semantics that differ from real artifact keys.
- Do not hide required prerequisites behind implicit assumptions.

### Git Intelligence Summary

- Recent commit pattern is story-scoped and pragmatic (`story 5.1`, `story 5.2`) with accompanying docs and tests.
- Follow the same approach: keep changes focused on reproducibility docs and only add code changes when behavior/documentation mismatches are concrete.

### Latest Technical Information

- Streamlit `1.56.0` is the latest stable release line and includes stable navigation/widget updates relevant to dashboard UX.
- PySpark `4.1.1` is the latest stable PyPI release; `4.2.x` currently appears as pre-release/dev.
- Azure Event Hubs SDK `5.15.1` is current stable; `5.x` remains the recommended line for new work.

### Project Context Reference

- No `project-context.md` was discovered; context sourced from planning and implementation artifacts.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 5, Story 5.3 definition)
- `_bmad-output/planning-artifacts/prd.md` (`FR31`, `NFR5`, `NFR6`)
- `_bmad-output/planning-artifacts/architecture.md` (orchestration boundaries, status contracts, dashboard debug/status intent)
- `_bmad-output/implementation-artifacts/5-2-display-pipeline-status-and-last-processed-batch.md` (status semantics and prior story lessons)
- [Streamlit 1.56.0 release](https://github.com/streamlit/streamlit/releases/tag/1.56.0)
- [PySpark on PyPI](https://pypi.org/project/pyspark/)
- [Azure Event Hubs SDK for Python](https://learn.microsoft.com/en-us/python/api/overview/azure/event-hubs?view=azure-python)

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- Updated sprint tracking state to `in-progress` at start of implementation.
- Added Story 5.3 runbook section in `README.md` and created `docs/demo_runbook.md`.
- Added docs validation tests in `tests/docs/test_demo_runbook_docs.py`.
- Executed targeted regression tests:
  - `python -m pytest tests/dashboard/test_demo_controls.py tests/dashboard/test_status_display.py tests/orchestration/test_demo_runner.py tests/docs/test_demo_runbook_docs.py`
- Executed full suite:
  - `python -m pytest` (102 passed).

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story prepared with cross-story continuity from 5.1 and 5.2 to maximize reproducible run reliability.
- Documentation-first implementation scope clarified with guardrails for when code changes are justified.
- Added reproducible PowerShell-first runbook flow covering setup, preflight, start/monitor/stop/reset, healthy vs stalled signals, and troubleshooting.
- Added explicit no-source-edit requirement and checkpoint semantics for `status`, `last_heartbeat_ts`, and `last_batch_ts`.
- Added docs validation tests to ensure runbook path and core lifecycle references remain present.
- Verified no regressions by running targeted and full pytest suites.
- Code review fixes applied: aligned stalled-signal guidance with heartbeat-approx behavior, expanded Linux/macOS parity in runbook checkpoints, added quick command blocks to README, and strengthened docs validation assertions.

### File List

- `_bmad-output/implementation-artifacts/5-3-provide-reproducible-demo-run-instructions.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `README.md`
- `docs/demo_runbook.md`
- `tests/docs/test_demo_runbook_docs.py`

### Change Log

- 2026-04-15: Implemented Story 5.3 reproducible demo instructions in README and dedicated runbook; added docs validation tests and verified full test suite pass.
- 2026-04-15: Addressed code-review findings by improving runbook signal semantics and cross-platform command parity, expanding README quick-run command coverage, and hardening docs tests.

## Senior Developer Review (AI)

### Reviewer

Javi

### Date

2026-04-15

### Outcome

Changes Requested -> Fixed Automatically

### Findings Resolved

- Updated runbook stalled/error detection guidance so it does not rely on `Batch Age` alone during heartbeat approximation mode.
- Added Linux/macOS alternatives for preflight and post-run verification command blocks where PowerShell-only coverage existed.
- Added quick start/launch command blocks in `README.md` so story claims about README command guidance are accurate.
- Strengthened `tests/docs/test_demo_runbook_docs.py` to validate key lifecycle/reproducibility sections rather than only a few string references.
