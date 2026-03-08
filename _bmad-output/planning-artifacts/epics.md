stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - path: "_bmad-output/planning-artifacts/prd.md"
    type: "prd"
  - path: "_bmad-output/planning-artifacts/architecture.md"
    type: "architecture"
  - path: "_bmad-output/planning-artifacts/prd-validation-report.md"
    type: "prd-validation-report"
---

# Stream_Analytics_Project - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Stream_Analytics_Project, decomposing the requirements from the PRD and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: The Student/Developer can configure and run a feed generator that produces two distinct event streams representing core food-delivery operations.
FR2: The Student/Developer can define and update AVRO schemas for each feed without changing generator code structure.
FR3: The Student/Developer can generate events in both JSON and AVRO formats for each feed.
FR4: The Student/Developer can configure generator parameters such as number of restaurants, couriers, zones, and demand levels.
FR5: The Student/Developer can enable or disable specific edge-case behaviors (late events, duplicates, missing steps, impossible durations, courier offline) via configuration.
FR6: The Student/Developer can produce small sample batches of events for inspection and debugging.

FR7: The Student/Developer can configure the generator to publish events to Azure Event Hubs.
FR8: The Student/Developer can specify Event Hubs connection settings (namespace, hub name, authentication parameters) via configuration files or environment.
FR9: The Student/Developer can define and adjust topic/partition/keying strategy for each feed.
FR10: The Professor/Grader can view documentation that explains the chosen topic/partition/key strategy and expected throughput.

FR11: The Student/Developer can configure and run Spark Structured Streaming jobs that consume the two feeds from Event Hubs.
FR12: The Student/Developer can define parsing and validation rules for incoming events, so that invalid records are routed to a dedicated error sink with a reason code while the streaming job continues running without failure.
FR13: The Student/Developer can enrich events with derived fields or reference data needed for analytics.
FR14: The Student/Developer can configure event-time semantics and watermarks for each stream.
FR15: The Student/Developer can define at least one basic windowed KPI computation over the event streams.
FR16: The Student/Developer can define at least one intermediate stateful or session-based metric over the event streams.
FR17: The Student/Developer can define at least one advanced anomaly or fraud-style metric that uses recent history and/or late data handling.
FR18: The Student/Developer can write curated outputs from Spark Structured Streaming into Parquet files on Azure Blob Storage.
FR19: The Professor/Grader can inspect the Parquet outputs to confirm that they match the documented schemas and metric definitions.

FR20: The Student/Developer can run a Streamlit application that connects to the aggregated outputs produced by Spark.
FR21: The Dashboard Viewer can see, on the Streamlit dashboard, at minimum the following KPIs updated on each refresh: total active orders, average delivery time over the last configured time window, and cancellation rate over the last configured time window.
FR22: The Dashboard Viewer can view at least one time-series chart that shows how metrics evolve over time.
FR23: The Dashboard Viewer can filter metrics and charts by zone.
FR24: The Dashboard Viewer can filter metrics and charts by restaurant.
FR25: The Dashboard Viewer can select a time window (for example last 15 minutes, 1 hour, or 24 hours) for displayed data.
FR26: The Dashboard Viewer can see a health/anomaly-oriented view that highlights, for each time window, the top N zones (configurable, default N ≤ 10) whose delivery-time anomaly score or stress index exceeds a configured threshold.
FR27: The Dashboard Viewer can identify which filters are currently active in the dashboard UI.

FR28: The Student/Developer can start a local demo mode from the Streamlit UI that triggers or guides generator and pipeline execution.
FR29: The Student/Developer can stop or reset the demo mode from the Streamlit UI without manually terminating multiple CLI processes.
FR30: The Student/Developer can see in the UI (a) generator status (Running/Stopped/Error), (b) streaming job status (Running/Stopped/Error), and (c) the timestamp of the last successfully processed batch, all updated at least every 10 seconds while the demo is running.
FR31: The Professor/Grader can follow documented steps to reproduce a typical demo run without modifying code.

FR32: The Student/Developer can run the generator in a “debug mode” that limits throughput to a configurable maximum (for example ≤ 100 events per second) and caps entity counts (for example ≤ 20 restaurants and ≤ 20 couriers), so that a target scenario can be reproduced end-to-end in under 60 seconds using a documented config flag (for example `mode=debug`).
FR33: The Student/Developer can inspect example events and schemas to understand how edge cases are encoded.
FR34: The Student/Developer can verify, through the dashboard or logs, that late/out-of-order events are being processed according to the configured watermarks.
FR35: The Student/Developer can verify, through metrics or sample queries, that duplicates and missing-step sequences are handled in a known, documented way.

FR36: The Student/Developer can produce a README that explains how to run the generator, pipeline, and dashboard for both sample and full demos.
FR37: The Student/Developer can maintain a design note that describes feed schemas, assumptions, and how they support the planned analytics.
FR38: The Student/Developer can document the implemented basic, intermediate, and advanced use cases and how they appear in the dashboard.
FR39: The Student/Developer can produce a short reflection document that explains key tradeoffs, limitations, and what would be needed for production readiness.

### NonFunctional Requirements

NFR1: Under typical demo conditions, the 95th-percentile end-to-end latency from event generation to updated dashboard metrics should be less than 15 seconds, as measured over at least a 5-minute demo run using wall-clock timestamps between generator emit and dashboard refresh.
NFR2: Under typical demo conditions for a single viewer on course-standard hardware, 90% of dashboard filter interactions (changing zone, restaurant, or time window) should complete with updated charts within 3 seconds, as measured from user action to visible update in a screen recording or log trace.

NFR3: The system must not process real customer data; all entities are represented with anonymous identifiers and synthetic attributes, and schemas and sample events must not contain names, emails, phone numbers, or real-world addresses, as verified by schema review and spot-checks on generated data.
NFR4: For the standard course deployment, authentication for the dashboard is not required; the dashboard must be reachable on localhost or a controlled lab network without a login step, as confirmed by running the documented demo flow.

NFR5: A new user familiar with the course environment should be able to set up and run the full demo in 45 minutes or less by following the provided README and design note, without needing to read source code, as validated by at least one fresh-user setup test.
NFR6: Under a documented “typical demo” load range (for example event rates and volumes defined in the README), the demo run path should complete without unhandled errors and without streaming job failure, with any invalid records handled via the error sink defined in FR12; this should be demonstrated in at least one full demo run without manual intervention.

### Additional Requirements

- Use the PySpark ETL Cookiecutter (`victor-lucio/pyspark-etl-cookiecutter`) as the starter for the Spark/ETL portion of the project, initialized via `pip install cookiecutter` and `cookiecutter https://github.com/victor-lucio/pyspark-etl-cookiecutter`.
- Implement an Azure-centric stack: Azure Event Hubs for ingestion, Spark Structured Streaming for processing, and Parquet outputs on Azure Blob/ADLS, all accessed from a Python-first stack (generator, Spark jobs, Streamlit).
- Treat AVRO schemas for order events and courier status as the contract between generator, Spark jobs, and dashboard, with deliberate schema evolution to avoid breaking joins, watermarks, and anomaly/ZSI metrics.
- Use the Streamlit UI as the primary control plane for demo lifecycle by triggering generator and Spark jobs (via shell/CLI helpers) and reading status/heartbeat artifacts such as `generator_status.json` and `spark_job_status.json`.
- Expose a single, denormalized Parquet dataset (for example `metrics_by_zone_restaurant_window`) as the primary analytics surface for the dashboard, keyed by `zone_id`, `restaurant_id`, and time window, and containing KPIs plus advanced metrics like Delivery Time Anomaly Score and Zone Stress Index.
- Enforce naming and structuring conventions: snake_case for all datasets, columns, and JSON fields; `window_start` and `window_end` for time-window columns; project packages organized into `generator/`, `spark_jobs/`, `dashboard/`, `orchestration/`, with shared utilities in `common/` and mirrored tests under `tests/`.
- Emit structured JSON logs from generator and Spark jobs with fields such as `timestamp`, `component`, `level`, `message`, and `details`, and status artifacts that include `status`, `last_heartbeat_ts`, `last_batch_ts`, and `debug_mode`.
- Implement a multi-page Streamlit app with at least an Overview page (KPIs/time-series plus filters), Health/Anomalies page (ZSI, anomaly scores, stressed zones), and Debug/Status page (pipeline status and debug indicators), reading aggregated Parquet outputs through a caching layer to balance freshness and responsiveness.
- Assume a deployment environment of local machine for generator and Streamlit, Azure Event Hubs and Spark for streaming and storage, and configuration stored in `config/` (YAML) and loaded via shared config utilities, with demo scripts that orchestrate runs consistent with the architecture document.

### FR Coverage Map

FR1: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds  
FR2: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds  
FR3: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds  
FR4: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds  
FR5: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds  
FR6: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds  
FR7: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR8: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR9: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR10: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR11: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR12: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR13: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR14: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR15: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR16: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR17: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR18: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR19: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data  
FR20: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR21: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR22: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR23: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR24: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR25: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR26: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR27: Epic 4 – Milestone 2 – Explore Real‑Time Operational Insights in the Dashboard  
FR28: Epic 5 – Milestone 2 – Orchestrate and Monitor End‑to‑End Demo Runs  
FR29: Epic 5 – Milestone 2 – Orchestrate and Monitor End‑to‑End Demo Runs  
FR30: Epic 5 – Milestone 2 – Orchestrate and Monitor End‑to‑End Demo Runs  
FR31: Epic 5 – Milestone 2 – Orchestrate and Monitor End‑to‑End Demo Runs  
FR32: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds (debug mode slice)  
FR33: Epic 1 – Milestone 1 – Design and Run Synthetic Food‑Delivery Feeds (edge‑case inspection)  
FR34: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data (late/out‑of‑order behavior)  
FR35: Epic 3 – Milestone 2 – Stream, Process, and Store Analytics‑Ready Data (duplicates/missing‑step handling)  
FR36: Epic 2 – Milestone 1 – Document and Explain Milestone 1 Feeds  
FR37: Epic 2 – Milestone 1 – Document and Explain Milestone 1 Feeds  
FR38: Epic 6 – Milestone 2 – Document and Reflect on Full Pipeline  
FR39: Epic 6 – Milestone 2 – Document and Reflect on Full Pipeline  

## Epic List

### Epic 1 (Milestone 1): Design and Run Synthetic Food‑Delivery Feeds
Students can configure and run realistic, edge‑case‑rich order and courier feeds in JSON/AVRO for later streaming analytics, including a debug mode for quick, low‑volume scenarios.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR32, FR33

### Epic 2 (Milestone 1): Document and Explain Milestone 1 Feeds
Students can produce the documentation needed to explain the Milestone 1 generator and feeds (schemas, assumptions, and basic run instructions).
**FRs covered:** FR36, FR37

### Epic 3 (Milestone 2): Stream, Process, and Store Analytics‑Ready Data
Students can stream events into Azure Event Hubs, process them with Spark Structured Streaming (including edge‑case handling and multiple analytics metrics), and write curated Parquet outputs ready for inspection and dashboard consumption.
**FRs covered:** FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR34, FR35

### Epic 4 (Milestone 2): Explore Real‑Time Operational Insights in the Dashboard
Viewers can use the Streamlit dashboard to see live KPIs, time‑series charts, and anomaly/health views, with filters for zone, restaurant, and time window.
**FRs covered:** FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27

### Epic 5 (Milestone 2): Orchestrate and Monitor End‑to‑End Demo Runs
Students and graders can start, stop, and reset a full demo from the UI, see clear generator and streaming‑job status, and reliably reproduce demo runs without manual CLI juggling.
**FRs covered:** FR28, FR29, FR30, FR31

### Epic 6 (Milestone 2): Document and Reflect on the Full Pipeline
Students can complete end‑to‑end documentation and reflection for the full pipeline, including implemented use cases and production‑readiness tradeoffs.
**FRs covered:** FR38, FR39

## Architecture Compliance Notes (Validation)

- **Starter template**: Architecture specifies a PySpark ETL Cookiecutter starter. This is captured as a requirement in the inventory, but there is not yet an explicit story that performs “starter template scaffolding” as the first implementation step. If you want strict compliance with the architecture decision, we should add a Milestone 1 story (ideally Story 1.0 or 1.1) that initializes the project using that cookiecutter.

## Epic 1: Design and Run Synthetic Food‑Delivery Feeds

Students can configure and run realistic, edge‑case‑rich order and courier feeds in JSON/AVRO for later streaming analytics, including a debug mode for quick, low‑volume scenarios.

### Story 1.1: Configure Core Feed Parameters

As a Student/Developer,  
I want to configure core generator parameters (zones, restaurants, couriers, demand levels),  
So that I can shape realistic food‑delivery scenarios for my demos.

**Acceptance Criteria:**

**Given** a documented configuration mechanism for the generator (for example a YAML file or CLI flags),  
**When** I specify values for number of zones, restaurants, couriers, and a demand level or rate,  
**Then** the generator uses those values when producing events (entity counts and event rates match configuration within documented tolerances).

**Given** I provide an invalid configuration value (for example a negative entity count),  
**When** I attempt to run the generator,  
**Then** the generator fails fast or rejects the config with a clear error message that identifies the invalid field.

### Story 1.2: Generate Two Distinct Operational Feeds

As a Student/Developer,  
I want to generate two distinct event streams (for example order events and courier status) in both JSON and AVRO formats,  
So that downstream streaming jobs can rely on well‑defined inputs.

**Acceptance Criteria:**

**Given** valid generator configuration for entities,  
**When** I run the generator in file or stream mode,  
**Then** it produces an order‑events feed and a courier‑status feed as distinct logical streams.

**Given** I configure the generator to output JSON,  
**When** I run it,  
**Then** it produces JSON events that validate against the documented order and courier schemas.

**Given** I configure the generator to output AVRO,  
**When** I run it,  
**Then** it produces AVRO events that validate against the AVRO schemas for both feeds and can be decoded by standard AVRO tooling.

### Story 1.3: Control Edge‑Case Behaviors via Configuration

As a Student/Developer,  
I want to enable or disable edge‑case behaviors (late events, duplicates, missing steps, impossible durations, courier offline) via configuration,  
So that I can teach or debug specific streaming scenarios on demand.

**Acceptance Criteria:**

**Given** edge‑case toggles and/or rates are defined in generator configuration,  
**When** I disable all edge‑case flags,  
**Then** the generator produces only “normal” events without late, duplicate, missing‑step, impossible‑duration, or courier‑offline behaviors (within documented random variation).

**Given** I enable a specific edge‑case flag (for example duplicates) at a non‑zero rate,  
**When** I generate a sufficiently large sample,  
**Then** the resulting events include that edge case at approximately the configured frequency and the encoding of the edge case matches the documented pattern.

### Story 1.4: Produce Small Sample Batches for Inspection

As a Student/Developer,  
I want to generate small, inspectable sample batches of events,  
So that I can quickly validate event shapes and values before wiring up the full pipeline.

**Acceptance Criteria:**

**Given** I run the generator in a documented “sample” mode or with parameters that cap total events,  
**When** I request a small batch (for example a few hundred events per feed),  
**Then** the generator produces a finite batch of events that can be opened in common tools (text editor, JSON viewer, AVRO decoder) without performance issues.

**Given** I inspect the sample batch,  
**When** I compare fields to the documented schemas,  
**Then** each event includes the required fields (for example IDs, event‑time, status fields) with reasonable, domain‑appropriate values.

### Story 1.5: Run the Generator in Debug Mode

As a Student/Developer,  
I want a low‑volume debug mode with capped throughput and entity counts,  
So that I can reliably reproduce scenarios end‑to‑end in under a minute using a documented debug flag.

**Acceptance Criteria:**

**Given** a documented debug configuration option (for example `mode=debug` or an equivalent flag),  
**When** I start the generator in debug mode,  
**Then** the generator limits throughput to a low, documented maximum (for example ≤ 100 events per second) and caps entity counts (for example ≤ 20 restaurants and ≤ 20 couriers).

**Given** I run the full demo pipeline using debug mode settings,  
**When** I follow the documented steps,  
**Then** a representative scenario (including at least one edge case) completes end‑to‑end within roughly one minute, suitable for quick iteration and troubleshooting.

### Story 1.6: Inspect Example Events to Understand Edge Cases

As a Student/Developer,  
I want to easily inspect example events and schemas for each edge case,  
So that I can see exactly how late/out‑of‑order, duplicate, missing‑step, and impossible‑duration scenarios are encoded.

**Acceptance Criteria:**

**Given** the generator documentation and sample outputs,  
**When** I look up each supported edge‑case type,  
**Then** I can find at least one concrete example event (or small set of events) that demonstrates how that edge case is represented in the data.

**Given** I compare those example events to the AVRO/JSON schemas,  
**When** I validate them,  
**Then** the example events conform to the schemas and clearly illustrate the intended edge‑case semantics (for example which fields indicate lateness, duplicates, missing steps, or impossible durations).

## Epic 2: Document and Explain Milestone 1 Feeds

Students can produce the documentation needed to explain the Milestone 1 generator and feeds (schemas, assumptions, and basic run instructions).

### Story 2.1: Write Generator and Feed Design Note

As a Student/Developer,  
I want to maintain a design note that describes the two feeds, their schemas, and key assumptions,  
So that graders and collaborators can understand how the data supports the planned analytics.

**Acceptance Criteria:**

**Given** the current generator implementation and AVRO/JSON schemas,  
**When** I update the design note,  
**Then** it clearly describes each feed’s purpose, core entities and IDs, event‑time fields, and how the data enables the Milestone 2 analytics (windows, joins, anomaly metrics).

**Given** edge‑case behaviors are supported in the generator,  
**When** I review the design note,  
**Then** it explicitly documents which edge cases exist (late, duplicate, missing‑step, impossible‑duration, courier‑offline) and how they are encoded in the events.

### Story 2.2: Document How to Run Milestone 1 Generator and Samples

As a Student/Developer,  
I want a README section that explains how to run the generator in sample and debug modes,  
So that a new user can produce representative data without reading source code.

**Acceptance Criteria:**

**Given** a fresh clone of the repository and the documented environment prerequisites,  
**When** a new user follows the README instructions for running the generator in sample mode,  
**Then** they can successfully produce small JSON/AVRO batches for both feeds without modifying code.

**Given** the README includes a documented debug mode flow,  
**When** a new user follows those steps,  
**Then** they can run the generator in low‑volume debug mode and observe at least one edge‑case scenario within about one minute of execution.

## Epic 3: Stream, Process, and Store Analytics‑Ready Data

Students can stream events into Azure Event Hubs, process them with Spark Structured Streaming (including edge‑case handling and multiple analytics metrics), and write curated Parquet outputs ready for inspection and dashboard consumption.

### Story 3.1: Publish Feeds to Azure Event Hubs

As a Student/Developer,  
I want to configure the generator to publish both feeds to Azure Event Hubs,  
So that downstream Spark Structured Streaming jobs can consume them in real time.

**Acceptance Criteria:**

**Given** valid Azure Event Hubs credentials and connection information,  
**When** I configure the generator with the documented Event Hubs settings and start it in streaming mode,  
**Then** order and courier events are successfully published to the intended Event Hubs entities with a clear partition/keying strategy.

**Given** the topic/partition/keying strategy is documented,  
**When** a grader reviews the documentation,  
**Then** they can see which keys are used (for example order_id, courier_id, zone_id) and why that strategy was chosen for throughput and analytics.

### Story 3.2: Ingest and Validate Events with Spark Structured Streaming

As a Student/Developer,  
I want Spark Structured Streaming jobs that ingest and validate events from Event Hubs,  
So that invalid records are routed to an error sink while the streaming job keeps running.

**Acceptance Criteria:**

**Given** the generator is publishing events to Event Hubs,  
**When** I start the ingestion Spark job with the documented configuration,  
**Then** valid events are parsed into structured DataFrames using the expected schemas.

**Given** some events are malformed or schema‑incompatible by design or by test data,  
**When** the ingestion job encounters them,  
**Then** those events are written to an error sink (for example structured logs or a dedicated dataset) with a reason code, and the streaming job continues running without failing.

### Story 3.3: Configure Event‑Time Semantics, Watermarks, and Windows

As a Student/Developer,  
I want to configure event‑time semantics, watermarks, and windowing in the Spark jobs,  
So that metrics properly handle late and out‑of‑order events.

**Acceptance Criteria:**

**Given** the ingestion and transformation jobs are running,  
**When** I inspect the Spark job definitions,  
**Then** they use an event‑time column and watermarks consistent with the PRD and documented edge‑case behavior.

**Given** I run the pipeline with a mix of on‑time and deliberately late/out‑of‑order events,  
**When** I review the resulting metrics and/or logs,  
**Then** late events are handled according to the configured watermarks (for example included within allowed lateness and ignored beyond it) and this behavior is observable and explainable.

### Story 3.4: Compute and Store Windowed KPIs and Advanced Metrics

As a Student/Developer,  
I want Spark jobs that compute windowed KPIs and at least one stateful/anomaly metric,  
So that downstream dashboards can show both basic performance and stressed/anomalous behavior.

**Acceptance Criteria:**

**Given** clean, structured streams from ingestion,  
**When** I run the KPI and analytics Spark jobs,  
**Then** they output a denormalized Parquet dataset (for example `metrics_by_zone_restaurant_window`) with keys like zone_id, restaurant_id, window_start, and window_end.

**Given** the PRD’s requirements for basic, intermediate, and advanced metrics,  
**When** I inspect the metrics dataset,  
**Then** I can find columns for core KPIs (for example active orders, average delivery time, cancellation rate) and at least one anomaly or stress index metric per zone/restaurant/time window.

### Story 3.5: Persist Curated Outputs in Parquet for Inspection

As a Professor/Grader,  
I want curated Parquet outputs that match the documented schemas and metric definitions,  
So that I can inspect and verify the analytics without reading streaming code.

**Acceptance Criteria:**

**Given** a successful run of the analytics jobs,  
**When** I navigate to the configured Parquet output location,  
**Then** I see partitioned Parquet files for the metrics dataset and can read them with standard tools (for example Spark, Python, or SQL readers).

**Given** I compare the Parquet schema and contents to the documented metric definitions,  
**When** I sample a few windows and entities,  
**Then** the data matches the expected shapes and semantics (correct types, reasonable value ranges, and consistent aggregation logic).

## Epic 4: Explore Real‑Time Operational Insights in the Dashboard

Viewers can use the Streamlit dashboard to see live KPIs, time‑series charts, and anomaly/health views, with filters for zone, restaurant, and time window.

### Story 4.1: Build Core KPI and Time‑Series Dashboard View

As a Dashboard Viewer,  
I want a core dashboard view with KPIs and time‑series charts,  
So that I can see how operational performance evolves over time.

**Acceptance Criteria:**

**Given** the metrics Parquet dataset is being populated,  
**When** I open the Streamlit app’s main page,  
**Then** I see at least the required KPIs (for example total active orders, average delivery time over the selected window, cancellation rate) and at least one time‑series chart.

**Given** I refresh or the app auto‑refreshes,  
**When** new metric data is available,  
**Then** KPI values and charts update to reflect the latest metrics within the overall end‑to‑end latency targets.

### Story 4.2: Implement Zone, Restaurant, and Time‑Window Filters

As a Dashboard Viewer,  
I want to filter metrics and charts by zone, restaurant, and time window,  
So that I can focus on specific parts of the operation and time ranges.

**Acceptance Criteria:**

**Given** there are metrics for multiple zones and restaurants,  
**When** I select a particular zone and/or restaurant in the UI,  
**Then** all KPIs and charts update to display only data for the selected slice, and the active filters are clearly indicated.

**Given** there are multiple supported time windows (for example last 15 minutes, 1 hour, 24 hours),  
**When** I change the time‑window selection,  
**Then** the dashboard recomputes and displays metrics over the new time window within the PRD’s responsiveness targets.

### Story 4.3: Add Health and Anomaly View

As a Dashboard Viewer,  
I want a health/anomaly‑oriented view,  
So that I can quickly identify stressed zones and anomalous behavior.

**Acceptance Criteria:**

**Given** advanced metrics such as anomaly scores or zone stress index are available in the metrics dataset,  
**When** I navigate to the health/anomalies page,  
**Then** I see a view that highlights, for each time window, the top N zones whose anomaly or stress metric exceeds a documented threshold.

**Given** I adjust filters (for example time window or zone selection),  
**When** I view the health page,  
**Then** the list of stressed/anomalous zones and any visual indicators update accordingly.

## Epic 5: Orchestrate and Monitor End‑to‑End Demo Runs

Students and graders can start, stop, and reset a full demo from the UI, see clear generator and streaming‑job status, and reliably reproduce demo runs without manual CLI juggling.

### Story 5.1: Start and Stop Demo from the Dashboard

As a Student/Developer,  
I want to start and stop a full demo run from the Streamlit UI,  
So that I do not have to juggle multiple CLI processes manually.

**Acceptance Criteria:**

**Given** the environment is configured and the necessary scripts are available,  
**When** I click the “Start Demo” control in the UI,  
**Then** the generator and required Spark jobs are started (directly or via orchestration helpers) and the dashboard indicates that the demo is running.

**Given** a demo run is in progress,  
**When** I click the “Stop Demo” or “Reset Demo” control,  
**Then** the associated processes are cleanly stopped or reset according to the documentation, without leaving orphaned jobs.

### Story 5.2: Display Pipeline Status and Last Processed Batch

As a Student/Developer,  
I want the dashboard to show generator and streaming‑job status and the timestamp of the last processed batch,  
So that I can quickly tell if the demo is healthy.

**Acceptance Criteria:**

**Given** the demo has been started,  
**When** I open the debug/status page in the dashboard,  
**Then** I see status indicators for generator and streaming jobs (for example RUNNING/STOPPED/ERROR) and a timestamp for the last successfully processed batch.

**Given** the demo is healthy and new data is flowing,  
**When** I wait at least the documented refresh interval (for example 10 seconds),  
**Then** the last‑batch timestamp updates to reflect recent processing activity.

### Story 5.3: Provide Reproducible Demo Run Instructions

As a Professor/Grader,  
I want clear instructions for reproducing a typical demo run,  
So that I can evaluate the project without modifying code or guessing steps.

**Acceptance Criteria:**

**Given** I have access to the repo and environment prerequisites,  
**When** I follow the demo run instructions in the README or demo runbook,  
**Then** I can start the demo, observe live metrics updating, and stop the demo without editing any source files.

## Epic 6: Document and Reflect on the Full Pipeline

Students can complete end‑to‑end documentation and reflection for the full pipeline, including implemented use cases and production‑readiness tradeoffs.

### Story 6.1: Document Implemented Use Cases and Dashboard Views

As a Student/Developer,  
I want documentation that explains the implemented basic, intermediate, and advanced analytics use cases and how they appear in the dashboard,  
So that graders can map rubric items directly to the running system.

**Acceptance Criteria:**

**Given** the final dashboard and metrics are implemented,  
**When** I review the use‑case documentation,  
**Then** it clearly identifies which dashboard pages, KPIs, and charts correspond to the required basic, intermediate, and advanced use cases in the PRD.

**Given** a grader is reading the documentation,  
**When** they follow references from each use case to the UI,  
**Then** they can quickly find and observe the corresponding behavior in the running dashboard.

### Story 6.2: Write Reflection on Tradeoffs and Production Readiness

As a Student/Developer,  
I want to write a short reflection on key tradeoffs, limitations, and steps toward production readiness,  
So that I can demonstrate understanding of how this educational project would evolve into a real system.

**Acceptance Criteria:**

**Given** the full pipeline implementation and NFRs from the PRD,  
**When** I complete the reflection document,  
**Then** it discusses at least the major tradeoffs made (for example performance vs simplicity, observability vs complexity), known limitations, and specific actions that would be required for production‑grade reliability, scaling, and governance.

**Given** a grader reads the reflection,  
**When** they compare it to the architecture and implementation,  
**Then** the reflection is consistent with the actual system and shows clear awareness of gaps between the current demo and a robust production deployment.

