# Story 2.2: Document How to Run Milestone 1 Generator and Samples

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,  
I want a README section that explains how to run the generator in sample and debug modes,  
so that a new user can produce representative data without reading source code.

## Acceptance Criteria

1. Given a fresh clone of the repository and the documented environment prerequisites, when a new user follows the README instructions for running the generator in sample mode, then they can successfully produce small JSON/AVRO batches for both feeds without modifying code.
2. Given the README includes a documented debug mode flow, when a new user follows those steps, then they can run the generator in low-volume debug mode and observe at least one edge-case scenario within about one minute of execution.

## Tasks / Subtasks

- [x] Task 1 (AC: #1) – Define prerequisites and environment setup
  - [x] Subtask 1.1 – List required tools (Python version, `pip`, `virtualenv`/`conda`, Azure CLI if applicable)
  - [x] Subtask 1.2 – Document how to create and activate the Python environment
  - [x] Subtask 1.3 – Document installing project dependencies from `requirements.txt` / `pyproject.toml`
- [x] Task 2 (AC: #1) – Document how to run the generator in sample mode
  - [x] Subtask 2.1 – Describe where generator configs live (e.g. `config/generator.yaml`) and which keys control sample mode
  - [x] Subtask 2.2 – Provide concrete CLI commands to run the generator in sample mode (JSON and AVRO outputs)
  - [x] Subtask 2.3 – Explain expected outputs and where sample files are written (paths, file naming patterns)
- [x] Task 3 (AC: #2) – Document how to run the generator in debug mode
  - [x] Subtask 3.1 – Explain the purpose of debug mode (low throughput, capped entities, fast end-to-end runs)
  - [x] Subtask 3.2 – Document the configuration flag(s) for debug mode (for example `mode: debug` and entity limits)
  - [x] Subtask 3.3 – Provide example CLI commands for running debug mode and how to verify at least one edge-case scenario appears
- [x] Task 4 (AC: #1, #2) – Align README instructions with architecture and PRD
  - [x] Subtask 4.1 – Ensure README references the generator configuration model used in the architecture document
  - [x] Subtask 4.2 – Cross-check that instructions support production of both JSON and AVRO outputs as required by the PRD
  - [x] Subtask 4.3 – Confirm that README guidance is consistent with NFR5 (setup ≤ 45 minutes for a new user)

## Dev Notes

- The README section for this story should live in the main `README.md` under a clearly labeled heading such as “Running the Milestone 1 Generator and Samples”.
- Use consistent naming and structure from the architecture document: generator configuration in `config/generator.yaml`, code under `stream_analytics/generator/`, and sample outputs in a predictable location (for example `data/samples/`).
- The generator CLI should expose simple, copy-pasteable commands for:
  - Creating small JSON sample batches for both feeds.
  - Creating small AVRO sample batches for both feeds.
  - Running in debug mode with capped throughput and entity counts.
- Document how generator logs and sample outputs can be inspected (e.g. open JSON in an editor, use AVRO tools or Python scripts to decode AVRO files) to validate that events match the schemas and include edge cases.
- Align the documentation with PRD FR1–FR6, FR32–FR33, and FR36; explicitly mention that the README flow is the main entry point for Milestone 1 data generation.

### Project Structure Notes

- Follow the architecture’s project structure recommendations:
  - Place generator code under `stream_analytics/generator/` with schemas in `stream_analytics/generator/schemas/`.
  - Keep configuration under `config/` (for example `config/generator.yaml`) and avoid hard-coding paths or credentials.
  - Ensure any new helper scripts or modules created for this story adhere to snake_case naming and live in the appropriate package (`generator/` or shared `common/` utilities).
- README commands should assume the standard entrypoints defined by the architecture (for example a `generator/cli.py` module or a console script) and should not rely on internal module paths.
- Make sure any references to debug mode, sample mode, or edge-case toggles use the same terminology and field names as the AVRO schemas and configuration model.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#story-2-2-document-how-to-run-milestone-1-generator-and-samples`]
- [Source: `_bmad-output/planning-artifacts/prd.md#data-generation-feeds`]
- [Source: `_bmad-output/planning-artifacts/prd.md#observability-debugging-edge-cases`]
- [Source: `_bmad-output/planning-artifacts/prd.md#documentation-reflection`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#project-structure-boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#implementation-patterns-consistency-rules`]

## Dev Agent Record

### Agent Model Used

GPT-5.1 (Cursor dev-story workflow)

### Debug Log References

- Generator logs (for example `logs/generator.log`) should capture sample-mode and debug-mode runs, including configuration used and any notable edge-case injections.

### Completion Notes List

- Story implementation should be considered complete when:
  - README prerequisites and environment setup instructions are validated on a fresh environment.
  - Sample-mode commands produce JSON and AVRO batches that validate against the schemas.
  - Debug-mode commands produce low-volume runs where at least one configured edge-case scenario is observable.
  - Instructions are consistent with architecture and PRD documents and align with NFR5 and NFR6.

- Implementation notes for this session:
  - Added a dedicated “Running the Milestone 1 Generator and Samples” section to `README.md` that documents prerequisites, environment setup, and end-to-end sample/debug flows.
  - Verified that `config/generator.yaml` already exposes the required sample and debug knobs (batch size, debug caps, output formats) and kept it as the authoritative configuration reference in the README.
  - Ran the full `pytest` suite successfully to confirm that documentation-aligned behaviors (sample and debug generation, edge cases, and serialization) remain passing.

### File List

- `README.md` – Updated with a “Running the Milestone 1 Generator and Samples” section, including sample-mode and debug-mode instructions and an explicit debug recipe that guarantees at least one observable edge-case scenario on a fresh clone.
- `config/generator.yaml` – Referenced as the authoritative configuration model for generator, sample, debug, and edge-case knobs (no additional changes introduced in this story).
- `stream_analytics/generator/cli.py` – Relied on as the CLI entrypoint that implements `--sample`, `--debug-sample`, `--debug-seed`, and `--output-dir` flags used in the documented flows.
- `stream_analytics/generator/base_generators.py` and `stream_analytics/generator/serialization.py` – Relied on for actual sample generation, edge-case application, and JSON/AVRO writing behavior described in the README.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` – Updated automatically by the code-review workflow to reflect the new Story 2.2 status.

### Change Log

- Added Milestone 1 generator run instructions (sample and debug modes) to `README.md`, including prerequisites and environment setup guidance.
- Clarified how event-time values are encoded in JSON samples (microseconds since UNIX epoch) and how this aligns with downstream timestamp handling.
- Documented a concrete, copy-pasteable debug-mode recipe (config changes plus CLI command) that ensures at least one observable edge-case scenario within about one minute on a fresh clone.
- Updated sprint tracking (`sprint-status.yaml`) so that Story 2.2 now reflects a status of `done` once these documentation changes are in place.
