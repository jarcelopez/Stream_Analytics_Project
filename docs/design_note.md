# Stream Analytics Generator Design Note (Excerpt for Story 1.1)

This design note documents the configurable parameters for the synthetic generator and how they relate to the PRD’s functional requirements FR1–FR6.

## Core Configurable Parameters

The generator is configured via `config/generator.yaml` and a small set of environment-variable overrides (prefix `GENERATOR_`). Configuration is loaded through a shared helper (`stream_analytics/common/config.py`) into a strongly-typed `GeneratorConfig` model (`stream_analytics/generator/config_models.py`).

Key parameters:

- `zone_count` – number of delivery zones to simulate.
- `restaurant_count` – number of restaurants.
- `courier_count` – number of couriers.
- `demand_level` – qualitative demand setting, one of `low`, `medium`, `high`.
- `events_per_second` – target aggregate event rate for the generator.
- `debug_mode_max_events_per_second` – upper bound for debug mode throughput (used in FR32).
- `debug_mode_max_entity_count` – upper bound for entity counts in debug mode.
- `sample_batch_size_per_feed` – default batch size for sample outputs (used in FR6/FR33).

All fields use `snake_case` naming to stay consistent across generator code, Spark jobs, and dashboard logic.

## Mapping to Functional Requirements (FR1–FR6)

.- **FR1 / FR4 – Configurable feeds and parameters**  
  The `GeneratorConfig` structure captures the primary knobs for feed configuration: entity counts and demand level. By centralising these in a single model and loading mechanism, later stories can wire generator logic and Spark jobs to the same configuration source. For Story 1.1 specifically, this implementation covers **configuration and validation only**; the actual event‑generation logic that consumes these values is introduced in later generator stories (for example Story 1.2 and beyond).

- **FR2 / FR3 – Schema-driven generation**  
  While AVRO schemas and dual JSON/AVRO outputs are introduced in later stories, `GeneratorConfig` provides the core dimensional parameters (zones, restaurants, couriers) that those schemas depend on.

- **FR5 – Edge-case control (future stories)**  
  Reserved fields such as `debug_mode_max_events_per_second`, `debug_mode_max_entity_count`, and `sample_batch_size_per_feed` are established here so that edge-case toggles and debug behaviors can be layered on without refactoring the configuration structure.

- **FR6 – Sample batches for inspection**  
  `sample_batch_size_per_feed` provides a default for small, inspectable batches, to be used when implementing sample-mode generation in later Milestone 1 stories.

## Notes on Acceptance Criteria Scope (Story 1.1)

Story 1.1 reuses acceptance criteria that describe end‑to‑end behavior (“the generator uses those values when producing events…”). Within this milestone, Story 1.1 is intentionally scoped to:

- Define and validate the configuration surface (`GeneratorConfig`, YAML, env overrides).
- Fail fast with clear, structured errors when configuration is invalid.

The behavioral aspects of AC1—verifying that emitted events and effective rates match the configured values within documented tolerances—are delivered when the actual generator logic is implemented in subsequent stories. Until then, AC1 should be interpreted as **partially satisfied** from a configuration perspective only.

## Validation and Error Handling

Validation rules on `GeneratorConfig` enforce:

- Non-negative, within-bounds counts for zones, restaurants, and couriers.
- Positive, bounded `events_per_second` targets suitable for course demos.
- Reasonable upper limits for debug/entity counts and sample batch sizes.

On validation failure, configuration loading fails fast and emits structured error logs using the shared logging helpers. Each error carries:

- `field` – the configuration field name.
- `reason` – human-readable explanation.
- `reason_code` – machine-readable code (for example `invalid_value`).

This pattern establishes the error-handling behavior that later generator and Spark stories will extend when dealing with invalid events and schemas.

