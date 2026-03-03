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

