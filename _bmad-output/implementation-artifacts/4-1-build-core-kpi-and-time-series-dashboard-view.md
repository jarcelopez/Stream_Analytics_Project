# Story 4.1: build-core-kpi-and-time-series-dashboard-view

Status: done

## Story

As a Dashboard Viewer,  
I want a core dashboard view with KPIs and time-series charts,  
so that I can see how operational performance evolves over time.

## Acceptance Criteria

1. Given the metrics Parquet dataset is being populated, when I open the Streamlit app main page, then I see at least these KPIs: total active orders, average delivery time over the selected time window, and cancellation rate, plus at least one time-series chart.
2. Given I refresh the page (or auto-refresh is active), when new metric data is available, then KPI values and charts update to reflect the latest metrics while preserving the latency targets for end-to-end freshness.

## Tasks / Subtasks

- [x] Create dashboard package skeleton for Epic 4 entrypoint (AC: 1,2)
  - [x] Add `stream_analytics/dashboard/__init__.py`.
  - [x] Add `stream_analytics/dashboard/app.py` as Streamlit entrypoint and register Overview page layout.
  - [x] Keep naming and structure aligned with `stream_analytics/*` module layout and `tests/*` mirroring.
- [x] Implement Overview data-access layer from curated Parquet outputs (AC: 1,2)
  - [x] Add helper(s) to load `metrics_by_zone_restaurant_window`-style dataset from configured path.
  - [x] Add cache strategy (TTL-based) to reduce repeated scans while keeping near-real-time updates.
  - [x] Handle "no data yet" state with explicit, user-friendly message.
- [x] Implement KPI cards in Overview page (AC: 1,2)
  - [x] Compute and render total active orders.
  - [x] Compute and render average delivery time for selected window.
  - [x] Compute and render cancellation rate for selected window.
  - [x] Ensure KPI formulas use consistent column names (`snake_case`) and UTC-compatible timestamps.
- [x] Implement at least one time-series chart in Overview page (AC: 1,2)
  - [x] Plot KPI trend over time using `window_start`/`window_end`.
  - [x] Ensure chart updates on rerun/refresh when new parquet rows are available.
  - [x] Keep chart logic ready for filter integration in Story 4.2.
- [x] Add dashboard configuration and run path documentation for Story 4.1 scope (AC: 1,2)
  - [x] Add/update `config/dashboard.yaml` keys for refresh cadence and data source path.
  - [x] Add README run snippet for launching Streamlit overview and expected KPI/chart behavior.
- [x] Add tests for core KPI and chart-prep logic (AC: 1,2)
  - [x] Add unit tests under `tests/dashboard/` for KPI calculations on representative sample data.
  - [x] Add tests for empty-data and malformed-column handling.
  - [x] Add test for refresh/caching behavior contract (cache returns fresh values after TTL).

## Dev Notes

- Build this story as the first story of Epic 4; there is no previous Epic 4 story intelligence available yet.
- This story should deliver only the core Overview experience; zone/restaurant/time-window filters are in Story 4.2 and health/anomaly view is Story 4.3.
- Existing project already has `stream_analytics/common/` and `stream_analytics/spark_jobs/`; dashboard code should follow the same package conventions and avoid duplicating shared config/loading helpers.
- Curated metrics are expected from Story 3.4/3.5 outputs and should be treated as the source of truth for dashboard KPIs.

### Technical Requirements

- Use Python + Streamlit as the dashboard framework (FR20-FR22 scope).
- Keep all new dataset/field names in `snake_case` and use `window_start`/`window_end` for time-window semantics.
- Read configuration from shared config flow (`config/*.yaml` + common loader), not ad-hoc hardcoded paths.
- Maintain synthetic-data-only assumptions (no PII fields introduced in dashboard transformations).
- Ensure behavior supports NFR targets: freshness visibility (<15s typical end-to-end) and responsive interaction baseline.

### Architecture Compliance

- Respect component boundaries:
  - `stream_analytics/spark_jobs/` writes curated parquet outputs.
  - `stream_analytics/dashboard/` reads curated outputs and does not write operational datasets.
  - Shared helpers remain in `stream_analytics/common/`.
- Keep observability-friendly behavior in UI states:
  - explicit loading state,
  - explicit empty-data state,
  - concise error state for missing/unreadable parquet.

### Library / Framework Requirements

- Streamlit baseline: align implementation with current stable Streamlit 1.56.x capabilities and compatibility notes.
- Spark/PySpark side assumptions from prior stories: watermark/window semantics already handled upstream; dashboard must consume windowed outputs without recomputing streaming logic.
- Keep dependencies minimal; use existing project dependency patterns unless a new package is strictly required.

### File Structure Requirements

- Expected new/updated files in this story:
  - `stream_analytics/dashboard/__init__.py` (new)
  - `stream_analytics/dashboard/app.py` (new)
  - `config/dashboard.yaml` (new or update)
  - `tests/dashboard/test_overview_kpis.py` (new)
  - `tests/dashboard/test_overview_data_loading.py` (new)
  - `README.md` (update run instructions if missing dashboard section)

### Testing Requirements

- Unit-test KPI calculations against deterministic fixture data.
- Unit-test chart-preparation dataframe transformation (time ordering, expected columns, null handling).
- Unit-test no-data and bad-schema fallback messages.
- Validate tests run under existing pytest setup without requiring live Spark/Event Hubs.

### Latest Technical Information

- Streamlit current stable line includes 1.56.0 (Mar 2026), with improved navigation and widget behavior; implementation should avoid deprecated experimental APIs.
- For upstream compatibility checks, current PySpark docs expose watermark and stateful-operation semantics in 4.1.x; dashboard logic should assume possible late-data effects are already represented in curated parquet outputs.

### Project Structure Notes

- Actual repository currently contains `stream_analytics/common/`, `stream_analytics/generator/`, `stream_analytics/publisher/`, and `stream_analytics/spark_jobs/`; `stream_analytics/dashboard/` is not present yet and is intentionally introduced by this story.
- Current tests do not include `tests/dashboard/`; add this folder and mirror existing test style.

### References

- `_bmad-output/planning-artifacts/epics.md` (Epic 4, Story 4.1 acceptance criteria)
- `_bmad-output/planning-artifacts/prd.md` (FR20-FR22, NFR1-NFR2)
- `_bmad-output/planning-artifacts/architecture.md` (frontend architecture, naming conventions, structure boundaries)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story tracking state)

## Dev Agent Record

### Agent Model Used

Codex 5.3

### Debug Log References

- N/A (story creation workflow output)
- `python -m pytest` (64 passed)

### Completion Notes List

- Comprehensive story context created from epics, PRD, and architecture artifacts.
- Story includes implementation guardrails for structure, naming, testing, and dashboard scope boundaries.
- Latest framework notes included for Streamlit/Spark compatibility awareness.
- Implemented dashboard package entrypoint and Overview rendering flow in `stream_analytics/dashboard/app.py`.
- Added typed dashboard config loading from `config/dashboard.yaml` with environment-variable override support.
- Added metrics parquet loading guardrails, required-column validation, empty-state UX, and TTL cache contract.
- Implemented KPI snapshot computation and time-series preparation using `window_start`/`window_end` semantics.
- Added dashboard unit tests for KPI computation, chart preparation, malformed schema handling, and cache refresh behavior.
- Validated full regression suite with `python -m pytest` (64 passed).
- Addressed code-review findings: added toggleable auto-refresh loop and explicit loading spinner state for Overview metrics retrieval.
- Updated caching integration to persist `MetricsCache` in Streamlit `session_state`, ensuring TTL behavior survives reruns.
- Added focused unit coverage for auto-refresh rerun scheduling behavior.

### File List

- `_bmad-output/implementation-artifacts/4-1-build-core-kpi-and-time-series-dashboard-view.md`
- `stream_analytics/dashboard/__init__.py`
- `stream_analytics/dashboard/app.py`
- `config/dashboard.yaml`
- `tests/dashboard/test_overview_kpis.py`
- `tests/dashboard/test_overview_data_loading.py`
- `README.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-04-15: Completed Story 4.1 implementation for Overview dashboard KPIs and time-series view, added dashboard configuration and documentation, and validated with full pytest regression run.
- 2026-04-15: Applied code-review fixes for Story 4.1 (auto-refresh, session-persisted TTL cache behavior, explicit loading state) and validated dashboard test suite (`7 passed`).
