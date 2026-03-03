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
```

You can override any of these values using environment variables before running the generator CLI. For example:

```bash
export GENERATOR_ZONE_COUNT=6
export GENERATOR_EVENTS_PER_SECOND=120
```

The generator CLI will merge environment overrides on top of the YAML configuration.

## Running the Generator CLI (Story 1.1)

During Story 1.1, the generator CLI is responsible for loading and validating configuration; later stories will add actual event generation. In other words, Story 1.1 fully implements the configuration and validation portions of its acceptance criteria, while the “generator uses those values when producing events” behavior is completed once the generator core is introduced in subsequent stories.

To load and print the resolved configuration:

```bash
python -m stream_analytics.generator.cli --print-config
```

If configuration is invalid (for example a negative zone_count), the CLI fails fast and emits a structured error describing which fields are invalid.

