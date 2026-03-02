stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
inputDocuments:
  - path: "_bmad-output/planning-artifacts/prd.md"
    type: "prd"
  - path: "_bmad-output/planning-artifacts/research/technical-python-real-time-analytics-food-delivery-pipeline-research-2026-03-02.md"
    type: "research"
workflowType: 'architecture'
project_name: 'Stream_Analytics_Project'
user_name: 'Javi'
date: '2026-03-02'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The system must implement an end-to-end real-time analytics pipeline for a synthetic food‑delivery platform, covering data generation, streaming ingestion, processing, storage, analytics, dashboarding, operability, and documentation. From the PRD, there are 39 functional requirements (FR1–FR39) organized into clear sections:

- Data Generation & Feeds (FR1–FR6): two AVRO-modeled feeds (Order Events, Courier Status) with JSON/AVRO generation, realistic distributions, and controllable edge cases (late, duplicates, missing steps, impossible durations, courier offline).
- Streaming Ingestion (FR7–FR10): configuration-driven publishing to Azure Event Hubs with an explicit topic/partition/keying and consumer-group strategy, all documented.
- Stream Processing & Storage (FR11–FR19): Spark Structured Streaming jobs that parse/validate/enrich events, apply event-time semantics with watermarks, compute basic/intermediate/advanced metrics, and write curated Parquet outputs to Azure Blob Storage.
- Analytics Dashboard & Insights (FR20–FR27): a Streamlit dashboard that reads aggregated outputs, exposes core KPIs and time-series views, supports filtering by zone/restaurant/time window, and surfaces a health/anomaly view (top stressed zones or anomaly scores).
- Demo Orchestration & Operations (FR28–FR31): the Streamlit UI must orchestrate a “demo run” end-to-end (start/stop pipeline) and provide a reproducible, documented demo flow without manual CLI juggling.
- Observability, Debugging & Edge Cases (FR32–FR35): a debug mode with constrained throughput/entity counts, explicit visibility into edge-case behavior, and verification that late/out-of-order/duplicates/missing steps are handled as designed.
- Documentation & Reflection (FR36–FR39): README, design note, use-case documentation, and reflection tying implementation details back to course learning outcomes and production-readiness tradeoffs.

The epics and stories (4 epics, ~20 stories) reinforce this structure: M1 focuses on generator and AVRO schemas; M2 covers Event Hubs ingestion, Spark processing and storage, analytics metrics (Delivery Time Anomaly Score, Zone Stress Index), dashboard, and demo operability and NFR validation.

**Non-Functional Requirements:**
The PRD defines 6 key NFRs (NFR1–NFR6) that strongly influence the architecture:

- **Performance & Latency:** typical 95th-percentile end-to-end latency from event generation to updated dashboard metrics must be < 15 seconds (NFR1), and most dashboard interactions must update within ~3 seconds on course-standard hardware (NFR2).
- **Security & Data Safety:** only synthetic, anonymous entities are allowed; schemas and generator must avoid PII-like fields (NFR3). Dashboard access is local/trusted with no authentication (NFR4), simplifying security but making schema/content discipline important.
- **Operability & Setup:** a new user should be able to set up and run the full demo in ≤ 45 minutes using just docs, not source-code spelunking (NFR5), and a typical demo run should complete without unhandled errors, with invalid records handled by the error sink (NFR6).

These NFRs push the architecture toward clear boundaries between components, simple run paths, and robust failure handling in streaming jobs.

**Scale & Complexity:**
The project is classified as a data/analytics backend with dashboard in a greenfield context, with medium complexity. However, the density of learning objectives (event-time streaming, watermarks, anomaly detection, orchestrated demo, NFR validation) means architectural clarity is critical.

- Primary domain: streaming analytics backend plus real-time dashboard for a synthetic food‑delivery platform.
- Complexity level: **medium**, with non-trivial streaming correctness and operability requirements.
- Estimated architectural components: on the order of 6–8 major components (generator + config, AVRO schemas & serialization, Event Hubs topics, Spark Structured Streaming jobs, Parquet storage layout, dashboard and its data access layer, plus orchestration/control path between UI and pipeline).

### Technical Constraints & Dependencies

- **Azure-centric stack:** The pipeline is explicitly designed around Azure Event Hubs, Spark Structured Streaming (likely on Databricks or similar), and Azure Blob/ADLS for Parquet storage, which constrains connector choices and deployment topologies.
- **Python-first implementation:** Generator, Spark jobs (PySpark), and dashboard are all Python-based, relying on AVRO libraries, PySpark, and Streamlit. This simplifies language fragmentation but means careful attention to packaging and environment management.
- **Schema-driven design:** AVRO schemas for Order Events and Courier Status are the contract between generator, streaming jobs, and analytics; schema evolution must be deliberate to avoid breaking joins, watermarks, and anomaly/ZSI computations.
- **UI as control plane:** The Streamlit app is not just a viewer but also the orchestration surface for demo runs (start/stop, debug mode, status indicators). This requires a robust but course-feasible way for the UI to trigger and observe generator and streaming jobs.
- **Course/environment constraints:** Single-developer, time-boxed milestones, and local/teaching-focused environments favor a simple deployment story (minimal external services beyond the core Azure components) and clear documentation over heavy operational tooling.

### Cross-Cutting Concerns Identified

- **Streaming correctness:** Handling late/out-of-order/duplicate/missing events is central to both the generator design and Spark jobs. Watermark configuration, window choices, and metric definitions must all align with the injected edge cases so that behaviors are visible and explainable in the dashboard.
- **Observability & debug-ability:** Error sinks, logs, status indicators, and a “debug mode” path are required so that students and graders can see what the pipeline is doing and reproduce issues quickly. This touches generator configuration, streaming job design, and the dashboard UI.
- **Data modeling for analytics:** Aggregated outputs must be laid out (schemas, partitioning, time bucketing) to support both required metrics (Delivery Time Anomaly Score, Zone Stress Index, KPIs) and dashboard filters (zone, restaurant, time window) without excessive complexity or latency.
- **Run orchestration & lifecycle management:** The demo run must be startable/stoppable from the UI, with clean lifecycle management of generator and streaming jobs and no orphaned processes, impacting how components are packaged and invoked.
- **Documentation as part of architecture:** Because setup and learning outcomes are first-class goals, documentation and design notes are effectively part of the architecture—they define how users move through the system and how architectural decisions are communicated.

## Starter Template Evaluation

### Primary Technology Domain

Python-based data/streaming backend with Spark Structured Streaming and a Streamlit dashboard, based on Azure Event Hubs → Spark → Parquet on Blob → Streamlit requirements.

### Starter Options Considered

- **FastStream Cookiecutter (cookiecutter-faststream)**  
  - Focus: modern Python streaming microservices over message brokers (Kafka/RabbitMQ/etc.).  
  - Provides: async app skeleton, strong dev tooling (pytest, mypy, black, ruff, bandit), Docker, CI, AsyncAPI docs.  
  - Pros: excellent for service-style streaming apps; good DX and modern tooling.  
  - Cons: not Spark‑centric; project structure and examples are oriented around FastStream apps rather than Spark Structured Streaming jobs and data pipelines.

- **PySpark ETL Cookiecutter (victor-lucio/pyspark-etl-cookiecutter)**  
  - Focus: data engineering projects using Python and Spark (ETL/ELT/streaming).  
  - Provides: opinionated layout for Spark code, configs, tests, and tooling (flake8/black etc.), aimed at PySpark workloads.  
  - Pros: aligns directly with Spark Structured Streaming requirements; gives a clean separation of jobs, configs, and tests that maps well to ingestion + KPI/anomaly jobs; easier to adapt to Event Hubs + Parquet scenario.  
  - Cons: not Streamlit‑aware and not Azure‑specific; you still define generator, dashboard, and Azure wiring.

### Selected Starter: PySpark ETL Cookiecutter

**Rationale for Selection:**
- Closely matches the **Spark Structured Streaming** portion of the architecture, which is central to your milestones and analytics (KPIs, anomaly scores, ZSI).
- Encourages a clear separation of Spark jobs, configuration, and tests, supporting your needs around event-time processing, watermarks, windowed metrics, and curated Parquet outputs.
- Uses standard Python tooling and layout that fits your Python‑first, Azure‑based stack and is appropriate for an intermediate developer level.
- Allows you to layer in the Python generator and Streamlit dashboard alongside a Spark‑oriented pipeline skeleton instead of forcing a microservice‑first structure.

**Initialization Command:**

```bash
pip install cookiecutter
cookiecutter https://github.com/victor-lucio/pyspark-etl-cookiecutter
```

(Executed in a clean directory when scaffolding the Spark/ETL portion of the project.)

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Python as primary language with a PySpark‑centric layout for ETL/streaming jobs.
- Preconfigured linting/formatting stack (e.g., flake8, black) to keep Spark job code consistent.

**Styling Solution:**
- Not applicable to UI directly; leaves dashboard styling to Streamlit, which matches your plan to keep UI simple and focus on analytics.

**Build Tooling:**
- Standard Python packaging (`requirements.txt` / optional `pyproject.toml`) and virtualenv/conda workflow, suitable for running on local machines and Spark clusters.
- Project structure aimed at simple deployment of Spark jobs to clusters/notebooks without heavy custom build systems.

**Testing Framework:**
- Pytest-based testing setup suitable for unit tests on generator‑like utilities, schema validation, and small Spark logic tests.
- Linting integrated into the workflow to catch common issues before running jobs.

**Code Organization:**
- Clear separation between:
  - Spark job entrypoints and core transformation logic.
  - Configuration (YAML/JSON/ENV) used to drive jobs.
  - Utility modules that can be reused across jobs.
- This maps well to your ingestion vs KPI/anomaly vs ZSI jobs and supports incremental addition of new analytics.

**Development Experience:**
- Opinionated but lightweight scaffolding for running and testing Spark jobs locally.
- Encourages documentation and configuration patterns that align with your NFRs around setup time and reproducible demos.
- Leaves room to integrate the Python generator and Streamlit dashboard while reusing the same tooling and packaging approach.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- **Analytical model for dashboard:** Single wide aggregated table (e.g. `metrics_by_zone_restaurant_window`) as the primary source for KPIs, anomaly scores, and Zone Stress Index, keyed by zone/restaurant/time window.
- **Pipeline orchestration model:** Streamlit UI controls demo lifecycle via simple shell/CLI calls and status/heartbeat data written by generator and Spark jobs (no separate control service).
- **Dashboard structure:** Multi-page Streamlit app with at least:
  - Overview page (filters + KPIs + time-series).
  - Health/Anomalies page (ZSI, anomaly scores, stressed zones).
  - Debug/Status page (demo status indicators, debug-mode info).

**Important Decisions (Shape Architecture):**
- **Error sink:** Invalid/failed events and schema issues are logged primarily as structured JSON logs (feed_type, payload, reason_code, timestamps), optimized for local inspection and teaching rather than long-term warehousing.
- **Dashboard caching:** Streamlit employs in-app caching of aggregated metric reads (e.g. cache for N seconds) to smooth refreshes and reduce repeated filesystem scans over Parquet.
- **Security posture:** Dashboard assumes localhost / trusted lab network and synthetic-only data; no authentication layer on Streamlit, matching PRD constraints.

**Deferred Decisions (Post-MVP):**
- Potential introduction of a more structured error Parquet dataset and/or queryable error views if time allows.
- Hardening of orchestration (e.g. a dedicated control API/service) for more realistic production-like operation.
- Additional dashboard pages or advanced views beyond the three core pages.

### Data Architecture

- **Aggregated metrics model:**  
  - Use a single, denormalized Parquet dataset as the primary analytics surface for the dashboard, with columns such as:
    - Keys: `zone_id`, `restaurant_id`, time window boundaries.
    - KPIs: active orders, delivery time stats, cancellation rate, etc.
    - Advanced metrics: Delivery Time Anomaly Score, Zone Stress Index, any stress/health flags.
  - Rationale: simplifies Spark job outputs and dashboard queries, keeps filter logic straightforward, and directly supports the rubric-required views.

- **Error handling and observability for data issues:**  
  - Invalid events (schema mismatch, parse failures, impossible values) are written to structured JSON logs with enough fields to debug issues and demonstrate streaming correctness concepts.
  - Rationale: JSON logs are easy to inspect locally and sufficient for course demonstrations; a Parquet error table is optional stretch scope.

- **Read pattern for dashboard:**  
  - Streamlit reads from the aggregated Parquet outputs but wraps these reads in a caching layer so that repeated UI interactions within a short interval don’t re-scan files unnecessarily.
  - Rationale: balances freshness with responsiveness and simplicity for a single-user demo workload.

### Authentication & Security

- **Dashboard access model:**  
  - No authentication layer for the Streamlit UI; it is intended to run on localhost or a controlled lab network, using only synthetic, anonymized data.
  - Rationale: aligns with PRD (no real compliance scope, synthetic entities only) and keeps demo friction low while still maintaining safe schema/content.

### API & Communication Patterns

- **Control and status communication:**  
  - Streamlit controls the demo primarily via:
    - Shell/CLI invocations or scripts to start/stop the generator and Spark streaming jobs.
    - Reading status/heartbeat artifacts (small files, flags, or simple status records) produced by those processes to render “Running/Stopped/Error” and last-batch timestamps.
  - No dedicated control microservice or HTTP API is introduced for orchestration in the MVP.
  - Rationale: keeps orchestration understandable and implementable within course scope while still fulfilling FR28–FR31 and the NFRs around setup and robustness.

### Frontend Architecture

- **Streamlit layout and navigation:**
  - Multi-page structure:
    - **Overview:** main KPIs, time-series charts, zone/restaurant/time-window filters.
    - **Health/Anomalies:** Delivery Time Anomaly Score, Zone Stress Index, stressed zones and SLA breaches.
    - **Debug/Status:** generator/streaming-job status, last processed batch timestamps, debug-mode indicators, and links/notes for inspecting logs and samples.
  - Rationale: separates “storytelling” views for evaluators from “debug/teaching” views for builders, keeping each page focused and less cluttered.

### Infrastructure & Deployment

- **Environment assumptions:**
  - Local developer machine for generator and Streamlit.
  - Azure Event Hubs and Spark Structured Streaming (e.g. Databricks or equivalent) as the managed streaming plane, writing Parquet to Azure Blob/ADLS.
  - Simple configuration-driven scripts/commands to bridge local components to Azure resources.
  - Rationale: matches the Azure-centric, course-focused setup while avoiding unnecessary additional infrastructure for the MVP.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
- Naming of Spark jobs, datasets, and columns.
- JSON field naming and error/log formats between generator, Spark, and dashboard.
- Project/test structure for PySpark jobs vs generator vs Streamlit.
- Event field naming and status/heartbeat formats used for orchestration and debug views.

### Naming Patterns

**Dataset & Column Naming Conventions:**
- Dataset (table/view) names are **snake_case, plural where appropriate**, e.g. `order_events_raw`, `courier_status_raw`, `metrics_by_zone_restaurant_window`.
- Columns use **snake_case** everywhere (generator objects, AVRO schemas, Spark DataFrames, Parquet, JSON sent to dashboard), e.g. `order_id`, `courier_id`, `zone_id`, `event_time`, `delivery_time_seconds`, `anomaly_score`, `zone_stress_index`.
- Time-window columns are named `window_start` and `window_end` for all windowed outputs.
- Boolean flags are `is_xxx` or `has_xxx`, e.g. `is_anomalous`, `is_stressed_zone`.

**Code Naming Conventions (Python + PySpark + Streamlit):**
- Python modules and files: **snake_case**, e.g. `generator_config.py`, `order_events_generator.py`, `streaming_kpis_job.py`, `dashboard_overview.py`.
- Python functions: **snake_case**, e.g. `build_order_events_stream()`, `compute_zone_metrics()`, `load_metrics_for_dashboard()`.
- Python classes (where used): **PascalCase**, e.g. `GeneratorConfig`, `MetricsRepository`.
- Variables: **snake_case**, e.g. `order_events_df`, `metrics_df`, `debug_mode_enabled`.

### Structure Patterns

**Project Organization (top-level guidance):**
- Keep **generator**, **spark_jobs**, and **dashboard** code in clearly separated Python packages or subdirectories (e.g. `generator/`, `spark_jobs/`, `dashboard/`), each with its own `__init__.py`.
- Tests are:
  - Under a top-level `tests/` directory, mirrored by package (e.g. `tests/generator/`, `tests/spark_jobs/`, `tests/dashboard/`).
  - Named `test_*.py` for pytest to pick up.
- Shared utilities (e.g. schema helpers, time-window utilities, logging helpers) live in a `common/` or `shared/` module and **must not** be redefined per job.

**Config & Environment:**
- Configuration lives in `config/` as `.yaml` or `.toml` files; environment-specific overrides are handled via environment variables, not separate hard-coded config files.
- All components (generator, Spark jobs, dashboard) read configuration through a small shared config loader (e.g. `common/config.py`) instead of manually parsing env/paths in many places.

### Format Patterns

**JSON & Error Formats:**
- JSON and log payloads use **snake_case** field names, consistent with column naming.
- Structured error/log entries share a minimal common shape:
  - `timestamp` (ISO 8601 string).
  - `component` (e.g. `"generator"`, `"spark_job"`, `"dashboard"`).
  - `event_type` or `feed_type` where applicable.
  - `level` (`"INFO"`, `"WARN"`, `"ERROR"`).
  - `message` (short human-readable description).
  - `details` (object with free-form structured context).
- Invalid event logs include:
  - `payload` (raw or sanitized sample).
  - `reason_code` (e.g. `"schema_mismatch"`, `"missing_field"`, `"impossible_duration"`).

**Date/Time Representation:**
- All event times and window boundaries in JSON are **ISO 8601 strings in UTC**; Spark columns use `timestamp` type and are named consistently (`event_time`, `window_start`, `window_end`).

### Communication Patterns

**Status / Heartbeat Artifacts:**
- Status files/records for demo orchestration use consistent keys:
  - `status` (`"RUNNING"`, `"STOPPED"`, `"ERROR"`).
  - `last_heartbeat_ts` (ISO timestamp).
  - `last_batch_ts` (for Spark).
  - `debug_mode` (`true`/`false`).
- Names for these artifacts are predictable and singular, e.g. `generator_status.json`, `spark_job_status.json`, and are the only sources the dashboard reads for status.

**Event Semantics Across Components:**
- Field names that express the same concept (e.g. `order_id`, `courier_id`, `zone_id`) are never renamed between generator, AVRO schemas, Spark, and Parquet; join conditions and filters must reuse these exact names.

### Process Patterns

**Error Handling:**
- Generator and Spark jobs **log and continue** for expected edge cases (late/out-of-order/duplicates/missing steps/impossible durations), using `reason_code`s for observability, rather than throwing unhandled exceptions.
- “Hard” configuration or infrastructure errors (missing config, failed connection to Event Hubs, etc.) are logged at `"ERROR"` level and surface clearly in the Debug/Status page.

**Loading & Debug States (Dashboard):**
- All Streamlit pages use a shared pattern for loading states:
  - Show a clear “Loading…” or “Waiting for data…” indicator when upstream data or status is not yet available.
  - When `debug_mode` is enabled, show a compact debug banner indicating that metric values may not reflect full production-like throughput.

### Enforcement Guidelines

**All AI Agents MUST:**
- Use **snake_case** for all fields, columns, and JSON keys that flow through the pipeline, and **PascalCase** only for Python class names.
- Place new Spark jobs, generator components, or dashboard modules into the agreed `generator/`, `spark_jobs/`, `dashboard/`, and `common/` structure, with tests mirrored under `tests/`.
- Use the shared structured logging shape (including `timestamp`, `component`, `level`, and `message`) for any new logs or error outputs.

**Pattern Enforcement:**
- When adding new code, agents should:
  - Reuse existing config loaders, logging helpers, and common utilities instead of reimplementing them.
  - Check that any new datasets, columns, or JSON fields follow the established naming patterns and are documented in README/design notes if visible outside a single module.
- Pattern updates (e.g. new required fields in status artifacts) must be reflected in both the architecture document and a central “conventions” section of the project README before being used in new code.

## Project Structure & Boundaries

### Complete Project Directory Structure

```markdown
Stream_Analytics_Project/
├── README.md
├── project_epics_stories.yaml
├── requirements.txt
├── pyproject.toml                # optional, if you choose modern packaging
├── .env.example                  # sample environment variables (no secrets)
├── config/
│   ├── generator.yaml            # generator defaults (entity counts, edge-case rates)
│   ├── spark_jobs.yaml           # Spark job configs (sources, sinks, window sizes)
│   └── dashboard.yaml            # Streamlit settings (refresh cadence, debug mode)
├── stream_analytics/             # main Python package
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py             # shared config loader for all components
│   │   ├── logging_utils.py      # structured JSON logging helpers
│   │   └── time_utils.py         # time/window helpers, timezone handling
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── schemas/
│   │   │   ├── order_events.avsc
│   │   │   └── courier_status.avsc
│   │   ├── entities.py           # zones, restaurants, couriers, customers
│   │   ├── config_models.py      # GeneratorConfig dataclasses
│   │   ├── base_generators.py    # core OrderEvent/CourierStatus generators
│   │   ├── edge_cases.py         # late/out-of-order/duplicates/missing/impossible durations
│   │   ├── serialization.py      # JSON/AVRO writers
│   │   └── cli.py                # CLI entrypoint for M1 runs
│   ├── spark_jobs/
│   │   ├── __init__.py
│   │   ├── ingestion.py          # Event Hubs → clean streaming DataFrames
│   │   ├── windowed_kpis.py      # core KPIs windows and Parquet outputs
│   │   ├── anomaly_scores.py     # Delivery Time Anomaly Score jobs
│   │   ├── zone_stress_index.py  # Zone Stress Index jobs
│   │   └── schemas.py            # Spark-side schema definitions / enforcement
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── app.py                # Streamlit multi-page registration
│   │   ├── overview_page.py      # KPIs + time-series + filters
│   │   ├── health_page.py        # anomalies, ZSI, stressed zones
│   │   └── debug_status_page.py  # pipeline status, debug indicators, links to logs
│   └── orchestration/
│       ├── __init__.py
│       ├── demo_runner.py        # helpers invoked by Streamlit to start/stop demo
│       └── status_files.py       # read/write generator_status.json, spark_job_status.json
├── scripts/
│   ├── run_demo_local.sh         # orchestrated local demo runner (optional .ps1 on Windows)
│   └── sync_schemas.sh           # helper for syncing AVRO/Spark schema definitions
├── status/
│   ├── generator_status.json
│   └── spark_job_status.json
├── logs/
│   ├── generator.log             # structured JSON lines
│   └── spark_jobs.log
├── tests/
│   ├── __init__.py
│   ├── generator/
│   │   ├── test_config_models.py
│   │   ├── test_entities.py
│   │   └── test_edge_cases.py
│   ├── spark_jobs/
│   │   ├── test_ingestion.py
│   │   ├── test_windowed_kpis.py
│   │   └── test_anomaly_zsi.py
│   └── dashboard/
│       ├── test_filters.py
│       └── test_status_display.py
└── docs/
    ├── design_note.md            # feed design, schemas, analytics rationale
    ├── demo_runbook.md           # demo steps and expected behaviors
    └── nfr_validation.md         # notes/results for NFR checks
```

### Architectural Boundaries

**API Boundaries:**
- No external REST API is exposed; all interaction is through:
  - Azure Event Hubs for streaming ingestion.
  - Streamlit UI for demo control and visualization.

**Component Boundaries:**
- `stream_analytics/generator/` owns all synthetic data generation and AVRO schema usage; it does not know about dashboard layout.
- `stream_analytics/spark_jobs/` owns ingestion, validation, enrichment, and metric computation; it only outputs Parquet datasets and status/heartbeat artifacts.
- `stream_analytics/dashboard/` is read-only on aggregated Parquet outputs and status files; it does not write operational data.
- `stream_analytics/orchestration/` is the only place where Streamlit triggers generator/Spark processes and manipulates status artifacts.

**Data Boundaries:**
- Raw synthetic events on disk (JSON/AVRO) are considered generator-internal and for debugging/samples.
- Curated Parquet in Blob/ADLS forms the contract between Spark jobs and the dashboard.
- Status JSON files in `status/` are the contract between orchestration logic and the dashboard’s Debug/Status page.

### Requirements to Structure Mapping

**M1-E1 – Milestone 1: Streaming Feed Design & Generator**
- Schemas & generator implementation:
  - `stream_analytics/generator/schemas/`
  - `stream_analytics/generator/entities.py`
  - `stream_analytics/generator/config_models.py`
  - `stream_analytics/generator/base_generators.py`
  - `stream_analytics/generator/edge_cases.py`
  - `stream_analytics/generator/serialization.py`
  - `stream_analytics/generator/cli.py`
- Documentation:
  - `docs/design_note.md`

**M2-E1 – Milestone 2: Stream Ingestion, Processing & Storage**
- Event Hubs ingestion and parsing:
  - `stream_analytics/spark_jobs/ingestion.py`
  - `stream_analytics/spark_jobs/schemas.py`
- Windowed KPIs and curated Parquet storage:
  - `stream_analytics/spark_jobs/windowed_kpis.py`
- Azure-specific configuration:
  - `config/spark_jobs.yaml`

**M2-E2 – Milestone 2: Analytics, Metrics & Dashboard**
- Delivery Time Anomaly Score and Zone Stress Index:
  - `stream_analytics/spark_jobs/anomaly_scores.py`
  - `stream_analytics/spark_jobs/zone_stress_index.py`
- Dashboard views:
  - `stream_analytics/dashboard/overview_page.py`
  - `stream_analytics/dashboard/health_page.py`
- KPI/metric data access helpers:
  - `stream_analytics/dashboard/app.py`

**M2-E3 – Milestone 2: Demo Orchestration & Operability**
- Orchestration and demo control:
  - `stream_analytics/orchestration/demo_runner.py`
  - `stream_analytics/orchestration/status_files.py`
  - `scripts/run_demo_local.sh`
- Debug mode and status surface:
  - `stream_analytics/dashboard/debug_status_page.py`
  - `status/*.json`
  - `logs/*.log`

### Integration Points

**Internal Communication:**
- Generator → Event Hubs → Spark jobs → Parquet → Dashboard, with status/heartbeat side-channels via `status/*.json`.
- Shared utilities in `stream_analytics/common/` are the only allowed cross-cutting Python dependency between generator, Spark jobs, and dashboard.

**External Integrations:**
- Azure Event Hubs and Spark (e.g. Databricks) are accessed only from generator/Spark jobs using configuration from `config/`.

**Data Flow:**
- Synthetic events are generated locally, published to Event Hubs, consumed and processed by Spark Structured Streaming into curated Parquet tables, then read by Streamlit for KPIs, anomalies, and ZSI visualizations.
