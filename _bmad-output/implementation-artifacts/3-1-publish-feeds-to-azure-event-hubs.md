# Story 3.1: Publish Feeds to Azure Event Hubs

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Student/Developer,  
I want to configure the generator to publish both feeds to Azure Event Hubs,  
so that downstream Spark Structured Streaming jobs can consume them in real time.

## Acceptance Criteria

1. Given valid Azure Event Hubs credentials and connection information, when I configure the generator with the documented Event Hubs settings and start it in streaming mode, then order and courier events are successfully published to the intended Event Hubs entities with a clear partition/keying strategy.
2. Given the topic/partition/keying strategy is documented, when a grader reviews the documentation, then they can see which keys are used (for example `order_id`, `courier_id`, `zone_id`) and why that strategy was chosen for throughput and analytics.

## Tasks / Subtasks

- [x] Task 1 (AC: #1) - Finalize Event Hubs configuration contract
  - [x] Subtask 1.1 - Confirm and document required environment variables (`EVENTHUB_CONNECTION_STRING` and optional per-feed hub overrides via `GENERATOR_EVENT_HUBS_ORDER_TOPIC` / `GENERATOR_EVENT_HUBS_COURIER_TOPIC`)
  - [x] Subtask 1.2 - Ensure `config/generator.yaml` remains the default source for feed hub names and supports env override behavior
  - [x] Subtask 1.3 - Validate configuration errors fail fast with clear messages (missing connection string, invalid or empty hub names)
- [x] Task 2 (AC: #1) - Implement dual-feed Event Hubs publishing flow
  - [x] Subtask 2.1 - Reuse generator output path that already emits both order and courier feeds; avoid duplicating generation logic
  - [x] Subtask 2.2 - Publish both feeds to their target Event Hubs in streaming mode with structured logging for publish attempts and failures
  - [x] Subtask 2.3 - Ensure publish code supports partition key assignment and handles full-batch retries safely
- [x] Task 3 (AC: #1, #2) - Define and apply partition/keying strategy
  - [x] Subtask 3.1 - Use deterministic keying aligned with analytics joins and locality (primary recommendation: partition by `zone_id` for order feed; validate courier strategy against expected Spark queries)
  - [x] Subtask 3.2 - Record trade-offs (ordering guarantees per key, distribution across partitions, and potential hot partitions)
  - [x] Subtask 3.3 - Verify strategy under debug/sample load and capture evidence in logs
- [x] Task 4 (AC: #2) - Update documentation for grader review
  - [x] Subtask 4.1 - Add/refresh Milestone 2 ingestion section in `README.md` with setup and run commands
  - [x] Subtask 4.2 - Document topic/partition/key strategy and expected throughput assumptions in `docs/design_note.md` or milestone notes
  - [x] Subtask 4.3 - Include troubleshooting guidance for common Event Hubs failures (auth, missing entity path, quota/throughput)
- [x] Task 5 (AC: #1, #2) - Add tests and validation checks
  - [x] Subtask 5.1 - Add unit tests for config resolution and validation of Event Hubs settings
  - [x] Subtask 5.2 - Add publisher-level tests with mocks/fakes for Event Hubs client interactions
  - [x] Subtask 5.3 - Run full test suite and confirm no regressions in generator sample/debug behavior

## Dev Notes

- Existing implementation context:
  - `azure_sender.py` already demonstrates Event Hubs publishing with `EventHubProducerClient`, environment-loaded credentials, and `zone_id`-based partitioning.
  - `config/generator.yaml` already includes Story 3.1 fields (`event_hubs_order_topic`, `event_hubs_courier_topic`) and documents env override keys.
  - Current sender script only publishes order events; this story should generalize to both feeds and integrate with project package conventions.
- Reuse-first rule:
  - Do not create parallel config loaders, ad-hoc serializers, or duplicate sender implementations.
  - Reuse `stream_analytics.common.config.load_typed_config`, `stream_analytics.generator.config_models.GeneratorConfig`, and current generator feed outputs.
- Key guardrails for implementation:
  - Keep all field names and config keys in snake_case.
  - Keep secrets out of code and out of committed files.
  - Keep publishing behavior observable through structured logs (`timestamp`, `component`, `level`, `message`, `details`).
  - Preserve compatibility with current local Windows/PowerShell developer flow.
- Suggested implementation surface:
  - Promote Event Hubs publishing into package code under `stream_analytics/generator/` (or `stream_analytics/orchestration/` if chosen), and keep script-level wrapper minimal.
  - Provide one clear CLI entrypoint for running Event Hubs stream publishing in demo workflows.

### Project Structure Notes

- Preferred placement for Story 3.1 code:
  - `stream_analytics/generator/` for feed-to-hub publishing logic and config model integration.
  - `stream_analytics/common/` only for shared utilities (config/logging), not Event Hubs business logic.
  - `tests/generator/` for unit tests of publisher and config behavior.
- Avoid placing core logic in repository-root ad-hoc scripts. Root scripts (like `azure_sender.py`) can remain thin wrappers or backward-compatible entrypoints.
- Preserve architecture conventions for status/log artifacts and naming:
  - Status values: `RUNNING`, `STOPPED`, `ERROR`.
  - Common status artifacts: `status/generator_status.json`, `status/spark_job_status.json`.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#story-3-1-publish-feeds-to-azure-event-hubs`]
- [Source: `_bmad-output/planning-artifacts/prd.md#streaming-ingestion`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#api-communication-patterns`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#implementation-patterns-consistency-rules`]
- [Source: `config/generator.yaml`]
- [Source: `azure_sender.py`]
- [External Source: `azure-eventhub` latest stable 5.15.1 (PyPI and Azure SDK changelog, Nov 2025)]
- [External Source: Databricks docs (Jan 2026) on using Event Hubs via Kafka connector in Lakeflow pipelines where third-party Event Hubs connector is unavailable]

## Dev Agent Record

### Agent Model Used

GPT-5.3 (Cursor create-story workflow)

### Debug Log References

- Capture publisher run diagnostics in generator logs with per-feed send counts, partition key used, and send failures with reason.
- Include simple timing metrics in logs to estimate publish throughput during demo/debug runs.

### Completion Notes List

- Story context prepared with implementation guardrails to prevent duplicate sender logic and config drift.
- Architecture, PRD, and current repository state were cross-referenced to align file placement and naming conventions.
- Web research added current SDK and connector caveats so implementation targets current ecosystem behavior.
- Implemented deterministic partition key assignment in publisher flow (`zone_id` for order feed, `courier_id` for courier feed with zone fallback).
- Added safe full-batch retry behavior (up to 3 retries) for transient Event Hubs send failures.
- Fixed publisher config override prefix to `GENERATOR_` so env overrides resolve correctly.
- Added Story 3.1 publisher test coverage for partition strategy, fail-fast hub-name validation, retry flow, and env prefix behavior.
- Updated `README.md` with Milestone 2 Event Hubs ingestion setup/run/troubleshooting guidance.
- Updated `docs/design_note.md` with Event Hubs routing, partition trade-offs, and retry/reliability details.
- Validation evidence: `pytest` full suite passed (`29 passed`).
- Story moved from `review` to `done` after code-review remediation.
- Code review fix: partition strategy is now feed-aware (`order_events` => `zone_id`, `courier_status` => `courier_id`) and no longer depends on default hub names.
- Code review fix: added regression test coverage for custom Event Hub name overrides to ensure partition strategy remains correct.
- Code review fix: corrected Dev Agent Record file list to match actual changed files for Story 3.1.

### File List

- `_bmad-output/implementation-artifacts/sprint-status.yaml` (workflow status tracking)
- `_bmad-output/implementation-artifacts/3-1-publish-feeds-to-azure-event-hubs.md` (story status and review record updates)
- `stream_analytics/publisher/event_hub_publisher.py` (partitioned dual-feed publishing, retry logic, config contract hardening)
- `tests/publisher/test_event_hub_publisher.py` (Story 3.1 unit tests for publisher behavior including custom hub override partitioning)
- `README.md` (Milestone 2 Event Hubs runbook and troubleshooting)
- `docs/design_note.md` (partition/key strategy and Event Hubs publishing rationale)

### Change Log

- 2026-04-14: Implemented Story 3.1 dual-feed Event Hubs publishing hardening (partition keys, retries, config validation), added tests, and updated reviewer-facing documentation.
- 2026-04-14: Code review remediation: fixed partition key behavior for custom hub names, expanded regression tests, corrected file list documentation, and moved story to done.

## Senior Developer Review (AI)

- Outcome: Changes requested during review were implemented and verified.
- High-severity issue fixed: partition key strategy now follows feed semantics rather than default hub-name equality checks.
- Medium-severity issue fixed: test coverage now includes custom Event Hub name overrides to prevent partitioning regressions.
- Documentation/tracing fixed: Dev Agent Record file list now aligns with actual repository changes for this story.
- AC re-validation:
  - AC1: Implemented (dual-feed publishing with deterministic partitioning and retry behavior).
  - AC2: Implemented (README and design note clearly document partition/key strategy and rationale).
