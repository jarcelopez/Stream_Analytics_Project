# Story 1.1: Configure Core Feed Parameters

Status: in-progress

- **Story ID**: 1.1  
- **Story Key**: 1-1-configure-core-feed-parameters  
- **Epic**: Epic 1 – Design and Run Synthetic Food‑Delivery Feeds  

## Story

As a Student/Developer,  
I want to configure core generator parameters (zones, restaurants, couriers, demand levels),  
so that I can shape realistic food‑delivery scenarios for my demos.

## Acceptance Criteria

1. **Configurable core parameters**
   - **Given** a documented configuration mechanism for the generator (for example a YAML file or CLI flags),  
     **When** I specify values for number of zones, restaurants, couriers, and a demand level or rate,  
     **Then** the generator uses those values when producing events (entity counts and event rates match configuration within documented tolerances).

2. **Clear handling of invalid configuration**
   - **Given** I provide an invalid configuration value (for example a negative entity count),  
     **When** I attempt to run the generator,  
     **Then** the generator fails fast or rejects the configuration with a clear error message that identifies the invalid field.

## Tasks / Subtasks

- [x] **T1 – Establish generator configuration model**
  - [x] Define a `GeneratorConfig` data model that captures zones, restaurants, couriers, demand levels, and any other core parameters needed for later stories (edge cases, debug mode, output formats).
  - [x] Implement config loading via `config/generator.yaml` (primary) plus environment variable overrides, using the shared config loader described in the architecture document.
  - [x] Document default ranges and recommended demo values (for example small defaults that make local testing fast).

- [x] **T2 – Wire configuration into the generator entrypoint**
  - [x] Create or extend a generator CLI entrypoint (for example `stream_analytics/generator/cli.py`) that loads `GeneratorConfig` before any event generation starts.
  - [ ] Ensure all entity counts and event rates used by the generator are driven exclusively by `GeneratorConfig` (no hard-coded “magic numbers” in generator logic) once event generation is implemented in later stories.
  - [x] Add a dry‑run or “print config” option that logs the resolved configuration (including defaults and overrides) before running, to make debugging easy.

- [x] **T3 – Implement validation and error reporting**
  - [x] Implement validation rules on `GeneratorConfig` (for example non‑negative counts, sensible upper bounds for demo workloads, required fields present).
  - [x] On validation failure, prevent the generator from starting and emit a structured error with a clear message and `reason_code` for each invalid field, following the logging conventions in the architecture document.
  - [x] Add at least one unit test per validation rule so regressions are caught early.

- [x] **T4 – Integrate with future edge‑case and debug mode support**
  - [x] Reserve configuration fields and structure that will be reused by later stories (edge‑case toggles, debug mode limits, sample batch sizes) so this story’s work does not need to be refactored heavily later.
  - [x] Ensure `GeneratorConfig` is easy to extend (for example using dataclasses or Pydantic models) and remains the single source of truth for generator behavior.

- [x] **T5 – Documentation and examples**
  - [x] Update the PRD‑aligned documentation or design note (for example `docs/design_note.md`) with a short section describing the configurable parameters and how they map to FR1–FR6.
  - [x] Add a short “Configuration” section to the README or generator README explaining how to adjust core parameters and where the config file lives.
  - [x] Provide at least one example `config/generator.yaml` snippet that corresponds to the default demo scenario.

## Dev Notes

- **Requirements alignment**
  - This story primarily covers FR1–FR6 slices related to configurability of the generator (especially FR1, FR4, FR6 and the setup for FR32/FR33) and underpins Epic 1 in `epics.md`.
  - Correct configuration handling here is a prerequisite for later ingestion, windowed metrics, anomaly scores, and dashboard behaviors described in the PRD and epics.

- **Architecture and design guardrails**
  - Follow the architecture document’s guidance to keep configuration in `config/generator.yaml` and load it via a shared config helper (for example `stream_analytics/common/config.py`), rather than scattering ad‑hoc `os.environ` reads or CLI parsing throughout the code.
  - Ensure configuration, logging, and any future status artifacts use `snake_case` field names consistently (for example `zone_count`, `restaurant_count`, `courier_count`, `demand_level`).
  - When emitting logs about configuration, follow the structured logging pattern (`timestamp`, `component`, `level`, `message`, `details`) so the Debug/Status dashboard page can surface them later without rework.

- **Operational expectations**
  - Default configurations should be chosen so that a full end‑to‑end demo (with later stories) comfortably meets the PRD’s NFRs, especially the `< 15s` end‑to‑end latency target and realistic but tractable event volumes.
  - The configured parameters should make it easy to run low‑volume “debug” scenarios later (for example small entity counts and lower event rates) while also supporting richer, higher‑volume scenarios for demonstration.

- **Error handling philosophy**
  - Misconfiguration is treated as a user/setup error: fail fast, explain clearly, and do not start the generator in an ambiguous state.
  - Edge‑case behavior toggles and more advanced validation are deferred to later stories, but this story should already establish the validation and error‑reporting patterns that future stories will extend.

### Project Structure Notes

- **Expected code locations (based on architecture document)**
  - Place generator code under `stream_analytics/generator/`, with:
    - `config_models.py` (or equivalent) defining `GeneratorConfig`.
    - `cli.py` containing the main CLI entrypoint and argument parsing.
    - `entities.py` and generator core modules reading from `GeneratorConfig` rather than hard‑coding counts.
  - Keep configuration files in `config/` (for example `config/generator.yaml`) and ensure the config loader is shared across generator, Spark jobs, and dashboard components as the architecture document recommends.
  - Mirror tests under `tests/generator/` (for example `tests/generator/test_config_models.py`, `tests/generator/test_cli_config_integration.py`).

- **Naming and consistency**
  - Use `snake_case` for all configuration keys and fields (for example `zone_count`, `restaurant_count`, `courier_count`, `demand_level`, `events_per_second`).
  - Use consistent terminology across config, code, PRD, and documentation (for example “zones”, “restaurants”, “couriers”, “demand level”) so future analytics stories can rely on stable names.

### References

- **Epics & Stories**
  - `_bmad-output/planning-artifacts/epics.md` – Epic 1 and Story 1.1 (“Configure Core Feed Parameters”), including BDD‑style acceptance criteria.

- **Product Requirements**
  - `_bmad-output/planning-artifacts/prd.md` – Functional Requirements FR1–FR6, FR32–FR33, and related NFRs describing generator configurability, debug mode, and edge‑case expectations.

- **Architecture**
  - `_bmad-output/planning-artifacts/architecture.md` – Sections on project structure, configuration patterns, naming conventions, and generator vs Spark vs dashboard boundaries.

## Dev Agent Record

### Agent Model Used

Cursor AI – GPT‑5.1 (`create-story` workflow)

### Debug Log References

- Generator configuration loading and validation are covered by unit tests in `tests/generator/test_config_models.py` and CLI integration tests in `tests/generator/test_cli_config_integration.py`. These tests exercise both valid configurations and failure paths with structured error logging.

### Completion Notes List

- “Ultimate context engine analysis completed – comprehensive developer guide for Story 1.1 created.”
- “Implemented `GeneratorConfig`, shared YAML + environment-based loading, and generator CLI wiring with validation and structured error reporting for configuration failures.”
- “Documented core generator parameters and defaults in `README.md` and `docs/design_note.md`, including an example `config/generator.yaml` snippet for the default demo scenario.”

### File List

- `stream_analytics/generator/config_models.py` – `GeneratorConfig` data model and validation.
- `stream_analytics/generator/cli.py` – generator CLI entrypoint using `GeneratorConfig`.
- `config/generator.yaml` – primary configuration file for generator parameters.
- `tests/generator/test_config_models.py` – unit tests for configuration validation.
- `tests/generator/test_cli_config_integration.py` – tests ensuring CLI and configuration integration behave as expected.
- `stream_analytics/__init__.py` – top-level package initialisation for the project.
- `stream_analytics/common/__init__.py` – shared utilities package initialisation.
- `stream_analytics/common/config.py` – shared YAML + environment config loader used by the generator (and later by Spark jobs and the dashboard).
- `stream_analytics/common/logging_utils.py` – structured JSON logging helpers used for configuration and error reporting.
- `stream_analytics/generator/__init__.py` – generator package initialisation.
- `tests/__init__.py` – test suite package initialisation.
- `tests/generator/__init__.py` – generator test package initialisation.
- `README.md` – project README including configuration section and generator CLI usage.
- `docs/design_note.md` – design note excerpt documenting generator configuration and its mapping to FR1–FR6.
- `_bmad-output/planning-artifacts/prd.md` – PRD document updated as part of Story 1.1 planning alignment.
- `_bmad-output/planning-artifacts/epics.md` – Epic and story breakdown updated to reflect Story 1.1.
- `_bmad-output/planning-artifacts/architecture.md` – Architecture document sections referenced and updated during Story 1.1.
- `_bmad-output/implementation-artifacts/1-1-configure-core-feed-parameters.md` – This story implementation document.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` – Sprint tracking status kept in sync with Story 1.1.

## Change Log

- 2026-03-02 – Implemented generator configuration model, loader, CLI wiring, validation, tests, and documentation for Story 1.1. Story status moved to `review`.


