# Stream Analytics Demo Project

This project implements a teaching-focused real-time analytics pipeline for a synthetic food-delivery platform.

The architecture centers on:

- A Python generator that produces synthetic order and courier events.
- Spark Structured Streaming jobs that ingest, validate, and aggregate events into Parquet datasets.
- A Streamlit dashboard that surfaces KPIs, time-series charts, and anomaly/health views.

For now, Story 1.1 focuses purely on configuring the generator; later stories flesh out the rest of the pipeline.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run tests:

```bash
pytest
```

## Running the Milestone 1 Generator and Samples

This section is the main entrypoint for Milestone 1 data generation (Story 2.2: “Document How to Run Milestone 1 Generator and Samples”) and is designed so a new student can follow it on a fresh clone without reading source code.

### Prerequisites

- **Python**: 3.10 or newer available on your PATH (`python --version`).
- **Pip and virtual environments**: `pip` plus either the built-in `venv` module or a tool like `conda` for creating isolated environments.
- **Git**: To clone this repository.
- **Optional tooling**: Azure CLI and related cloud tools are not required for Milestone 1 but will be useful in later milestones.

### Create and activate a Python environment

From the project root (`Stream_Analytics_Project`), run one of the following:

- **Using `venv` (recommended)**:

  ```bash
  python -m venv .venv
  # On macOS / Linux
  source .venv/bin/activate
  # On Windows (PowerShell)
  .venv\Scripts\Activate.ps1
  ```

- **Using `conda`** (if you prefer):

  ```bash
  conda create -n stream_analytics_demo python=3.10
  conda activate stream_analytics_demo
  ```

Then install dependencies:

```bash
pip install -r requirements.txt
```

At this point you have everything needed to run the generator in **sample** and **debug** modes.

## Generator Configuration

Core generator parameters live in `config/generator.yaml`. These values drive how many zones, restaurants, and couriers the generator will simulate, along with an overall demand level and events-per-second target for demos.

Example (default demo scenario):

```yaml
zone_count: 3
restaurant_count: 10
courier_count: 15
demand_level: medium  # one of: low, medium, high
events_per_second: 50
debug_mode_max_events_per_second: 100
debug_mode_max_entity_count: 20
sample_batch_size_per_feed: 500

output_base_dir: "samples/generator"
output_formats:
  - json
  - avro
```

Two important implementation details to keep in mind when inspecting samples:

- **Event times** in the JSON feeds are represented as **microseconds since UNIX epoch (UTC)** in an `event_time` integer field. Downstream Spark jobs will convert this into proper `timestamp` columns and align with the architecture’s ISO-8601 time semantics.
- **Edge-case rates** (`late_event_rate`, `duplicate_rate`, `missing_step_rate`, `impossible_duration_rate`, `courier_offline_rate`) default to `0.0`, meaning a fresh clone will not emit edge cases until you explicitly turn them on for a debug run.

You can override any of these values using environment variables before running the generator CLI. For example (note that `GENERATOR_OUTPUT_FORMATS` expects a JSON list string):

```bash
export GENERATOR_ZONE_COUNT=6
export GENERATOR_EVENTS_PER_SECOND=120
export GENERATOR_OUTPUT_BASE_DIR="data/samples"
export GENERATOR_OUTPUT_FORMATS='["json"]'
```

The generator CLI will merge environment overrides on top of the YAML configuration.

## Running the Generator CLI

### Print resolved configuration

To load and print the resolved configuration:

```bash
python -m stream_analytics.generator.cli --print-config
```

If configuration is invalid (for example a negative `zone_count` or an unsupported `output_formats` value), the CLI fails fast and emits a structured error describing which fields are invalid.

### Generate sample feeds (Story 1.2)

Story 1.2 adds a sample mode that generates small JSON and AVRO batches for both feeds:

- `order_events`
- `courier_status`

By default, running:

```bash
python -m stream_analytics.generator.cli --sample
```

will:

- Load `GeneratorConfig` from `config/generator.yaml` (plus any `GENERATOR_` env overrides).
- Use `output_base_dir` and `output_formats` to decide where and how to write data.
- Produce:
  - JSON:
    - `samples/generator/order_events/json/sample.jsonl`
    - `samples/generator/courier_status/json/sample.jsonl`
  - AVRO:
    - `samples/generator/order_events/avro/sample.avro`
    - `samples/generator/courier_status/avro/sample.avro`

To override the base output directory from the CLI, use:

```bash
python -m stream_analytics.generator.cli --sample --output-dir data/samples
```

In that case, the same relative layout (`order_events/json`, `courier_status/avro`, etc.) is created under `data/samples/`.

These samples are intended for:

- Quickly inspecting event shapes (JSON files) with a text editor or JSON viewer.
- Verifying AVRO compatibility using standard tooling.
- Feeding future Spark ingestion tests that read the JSON/AVRO outputs directly.

### Debug/sample runs and edge cases

For reproducible, low-volume demo runs you can enable a debug-style run:

```bash
python -m stream_analytics.generator.cli --sample --debug-sample --debug-seed 42
```

This:

- Uses the same schemas and generators as normal sample runs.
- Clamps entity-related knobs via `debug_mode_max_entity_count` to keep batches small and easy to inspect (for example ≤ 20 restaurants and ≤ 20 couriers by default).
- Clamps the effective `events_per_second` configuration to `min(events_per_second, debug_mode_max_events_per_second)` so that debug settings stay within a documented low-throughput ceiling (default ≤ 100 events/second across feeds); in sample/debug mode this primarily shapes future streaming behavior and sizing while the generator writes a small bounded batch.
- Seeds the generator so that repeating the command with the same configuration and `--debug-seed` yields identical sample outputs.

On a typical laptop, the default debug configuration produces both feeds and writes JSON/AVRO artifacts in well under a minute, while emitting structured log records (for example `component="generator_cli"` and `component="generator_edge_cases"`) that capture the effective debug settings and batch sizes for graders to inspect.

To **observe at least one edge-case scenario within about one minute** on a fresh clone (Story 2.2 AC2), follow this explicit debug recipe:

1. Open `config/generator.yaml` and set non-zero edge-case rates, for example:

   ```yaml
   late_event_rate: 0.2
   duplicate_rate: 0.2
   missing_step_rate: 0.1
   impossible_duration_rate: 0.1
   courier_offline_rate: 0.1
   ```

   These values keep the batch small but make it very likely that at least one event in each category appears in a single debug run.

2. From the project root, run:

   ```bash
   python -m stream_analytics.generator.cli --config-path config/generator.yaml ^
       --sample --debug-sample --debug-seed 42 --output-dir samples/generator
   ```

3. Inspect the outputs under `samples/generator/**`:

   - Use a text editor or JSON viewer on the JSON files to spot:
     - Negative time shifts (late events) via `event_time` comparisons.
     - Duplicated `order_id` values.
     - Gaps in expected lifecycle statuses (missing steps).
     - Very large `delivery_time_seconds` values (impossible durations).
     - `courier_status` records where `status="OFFLINE"` but `active_order_id` is non-null.
   - Use AVRO tools or Python readers to validate that the AVRO files remain schema-compatible even with edge cases applied.

This combination of configuration and command satisfies the Story 2.2 debug-mode acceptance criteria: a new user following these steps will produce a low-volume batch where at least one edge case is observable in well under a minute.

Checked-in JSON and AVRO sample artifacts under `samples/generator/**` provide concrete examples of these batches; see `docs/design_note.md` for a deeper mapping to FR6, FR32, FR33, and related generator stories.

### End-to-end debug demo (AC2)

To exercise the Story 1.5 “Run the generator in debug mode” acceptance criteria end-to-end for the generator and downstream teaching pipeline:

1. **Generate a debug demo batch** (satisfies the generator side of AC2):

   ```bash
   python -m stream_analytics.generator.cli --config-path config/generator.yaml ^
       --sample --debug-sample --debug-seed 42 --output-dir samples/generator
   ```

   - Produces capped, low-volume JSON/AVRO batches for both `order_events` and `courier_status` under `samples/generator/**`.
   - Keeps effective throughput under the configured debug ceilings so that a full run completes in roughly one minute on a typical laptop.

2. **Feed the debug batch into the streaming pipeline** (once Milestone 2 streaming jobs are wired up):

   - Use the same generator configuration and debug command as above.
   - Configure Spark Structured Streaming jobs to read from the JSON/AVRO outputs (or the corresponding Event Hubs topics in Milestone 2).
   - Persist curated outputs to Parquet and point the Streamlit dashboard at those Parquet locations.

3. **Observe edge cases and KPIs in the dashboard**:

   - With non-zero edge-case rates in `config/generator.yaml`, at least one edge-case scenario (late events, duplicates, missing steps, impossible durations, or courier offline with active orders) should be visible during a short debug run.
   - The debug demo pipeline should be suitable for quick iteration and troubleshooting during grading and live sessions.


