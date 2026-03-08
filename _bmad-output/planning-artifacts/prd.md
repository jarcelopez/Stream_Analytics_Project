---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation-skipped
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
inputDocuments:
  - path: "_bmad-output/brainstorming/brainstorming-session-2026-03-02-0001.md"
    type: "brainstorming"
  - path: "_bmad-output/planning-artifacts/research/technical-python-real-time-analytics-food-delivery-pipeline-research-2026-03-02.md"
    type: "research"
workflowType: 'prd'
documentCounts:
  briefCount: 0
  researchCount: 1
  brainstormingCount: 1
  projectDocsCount: 0
project_name: "Stream_Analytics_Project"
user_name: "Javi"
date: "2026-03-02"
classification:
  projectType: "data-analytics-backend-with-dashboard"
  domain: "streaming-analytics-education-simulated-food-delivery"
  complexity: "medium"
  projectContext: "greenfield"
---

# Product Requirements Document - Stream_Analytics_Project

**Author:** Javi
**Date:** 2026-03-02

## Executive Summary

This project delivers a realistic, course-feasible real-time analytics platform for a synthetic food-delivery service. It focuses on a Python-based streaming pipeline that ties together Avro event schemas, streaming infrastructure, and analytics logic to show end-to-end how operational events become actionable insight. The system simulates key entities and flows in a food-delivery platform—orders, couriers, restaurants, and edge situations—so that students and evaluators can see concrete, data-driven behavior rather than abstract examples.

### What Makes This Special

The project’s strength is its rich, well-structured streaming data and realistic behavior, not superficial differentiation. It emphasizes accurate simulation of the food-delivery domain while integrating edge cases directly into the event streams, enabling meaningful analysis of late events, anomalies, and operational friction. By combining Avro-based schemas, streaming ingestion, and real-time analytics focused on business questions, it clearly demonstrates how to turn a continuous flow of operational events into business understanding and value.

## Project Classification

- **Project Type:** Data/analytics backend with dashboard (streaming pipeline plus GUI for dashboards)
- **Domain:** Streaming/analytics education with a simulated food-delivery platform
- **Complexity:** Medium (realistic scenarios and edge cases without full production scope)
- **Project Context:** Greenfield (new system designed specifically for this course project)

## Success Criteria

### User Success

- Viewers can clearly see that the dashboard is driven by continuously arriving data (metrics and charts change as new events arrive) and use it to explain what is happening operationally (by zone/restaurant/courier/order flow).
- The “aha” moment is an unmistakably time-driven experience: charts and KPIs visibly evolve over time (e.g., per-window updates), showing the difference between “live operational state” vs static reporting.
- Users can answer insight questions from the dashboard without digging into raw data, e.g.:
  - Which zones are currently overloaded and why?
  - Are delivery times spiking (and where)?
  - Are cancellations/refunds clustering by zone/restaurant/time?

### Business Success

- All course-required deliverables are complete and professional:
  - Private GitHub repo with clear README, team structure, design note (fields/events/assumptions/planned analytics)
  - Python feed generator + usage README
  - AVRO schemas (with sensible types/enums/optional fields and versioning considerations)
  - Sample JSON + AVRO batches
  - Milestone 2 documentation covering ingestion/topic design and processing choices
  - Reflection summary on streaming tradeoffs and production-readiness gaps
- The project demonstrates the course learning outcomes: streaming models, brokers, JSON/AVRO formats, event-time processing, watermarks, windows, and streaming analytics patterns.

### Technical Success

- **Timeliness:** End-to-end “live insight” latency is typically **< 15 seconds** from ingestion to dashboard-visible metric changes (as observed during demo runs).
- **Feeds & schemas (M1):**
  - Two distinct feeds that represent core food-delivery operational dynamics, with justification for why they are essential and what analytics they enable.
  - Both feeds generated in **JSON and AVRO**, with clear schema evolution/versioning considerations.
  - Events include event-time fields and join identifiers (`order_id`, `restaurant_id`, `courier_id`, `zone_id`, etc.).
  - Generator supports realistic distributions (peaks, weekday/weekend, zone skew), configurability (supply/demand, surges, cancellations, promos), and streaming-correctness edge cases (late/out-of-order, duplicates, missing steps, impossible durations, courier offline mid-delivery).
- **Ingestion (M2):**
  - Two feeds are streamed into **Azure Event Hubs**.
  - Topic/partition/key design is documented, including expected throughput and consumer group strategy.
- **Stream processing (M2):**
  - Spark Structured Streaming jobs implement parsing/validation and enrichment.
  - Event-time processing is used, including **watermarks** and appropriate **windowing** (tumbling/hopping/sliding/session as relevant).
  - Outputs include:
    - Curated data at rest in **Parquet** on Azure Blob Storage
    - Aggregated metrics suitable for dashboard consumption
  - Use cases implemented:
    - Basic: windowed KPIs
    - Intermediate: at least one stateful/session-based metric
    - Advanced: at least one anomaly/fraud/forecasting-style metric with late data handling considered
- **Dashboard (M2):**
  - Live dashboard implemented in Streamlit (or PowerBI/Grafana/ELK) with a variety of real-time metrics and graphs, including filtering by zone/restaurant and at least one “health” view (alerts/SLA breaches/anomalies).

### Measurable Outcomes

- Demo run shows dashboard metrics updating continuously with **typical < 15s** lag.
- Evidence that edge cases exist and are handled/observable:
  - Late/out-of-order events do not break the pipeline; windows/watermarks behave as intended.
  - Duplicates and missing-step sequences are tolerated (or explicitly flagged) without crashing jobs.
  - “Impossible” durations generate measurable anomaly signals.
- Each required use-case tier (Basic/Intermediate/Advanced) is demonstrably implemented and produces interpretable dashboard outputs.

## Product Scope

### MVP - Minimum Viable Product

- Two feeds + AVRO schemas + JSON/AVRO event generation
- Realistic, configurable generator with required edge cases
- Event Hubs ingestion with documented topic design
- Spark Structured Streaming processing with event-time + watermarks + windowing
- Parquet outputs to Blob Storage + aggregated metrics
- Live dashboard with multiple KPIs/graphs, zone/restaurant filtering, and at least one health/anomaly view
- Required documentation + reflection summary

### Growth Features (Post-MVP)

- Stronger data quality tooling: schema validation tests, automated sample generation, reproducible seeds
- Better operational visibility: pipeline health metrics (processing rate, backlog), structured logging, basic alerting
- Richer analytics: more derived metrics, better drilldowns, cross-entity joins, more anomaly explanations
- CI checks: linting, unit tests, minimal integration tests for schema + sample pipeline

### Vision (Future)

- Production readiness: stronger reliability guarantees, scaling strategy, backpressure handling, replayability, cost controls
- Better governance: schema registry, formal data contracts, lineage, access control
- More advanced modeling: near-real-time forecasting, causal signals, robust fraud detection, experimentation support

## User Journeys

### Journey 1 — Student/Developer (Builder) success path (Milestone 1 → ready for feedback)

**Opening scene:** It’s early Milestone 1. You have a rubric, a one-week deadline, and you need to design two feeds that will actually enable Milestone 2 analytics (windows, watermarks, late data).

**Rising action:** You make a set of deliberate design choices:
- Choose two event feeds that represent core food-delivery dynamics and justify why they matter.
- Define AVRO schemas with event-time + join IDs, plus versioning considerations.
- Implement a configurable generator that produces both JSON and AVRO and includes realistic distributions (peaks, zone skew) and edge cases (late/out-of-order, duplicates, missing steps, impossible durations).

**Climax:** You run a short end-to-end “sanity demo” locally: sample batches look realistic, schemas validate, and the generator can reliably reproduce scenarios you can later explain in Milestone 2.

**Resolution:** You ship Milestone 1 deliverables (repo, README/design note, generator README, schemas, sample batches) and get actionable feedback that confirms your data design supports event-time processing and late data handling.

### Journey 2 — Student/Developer (Builder) edge-case/debugging path (the “it’s not working” week)

**Opening scene:** You’re integrating pieces (or validating Milestone 1 realism) and something breaks: events don’t match schema expectations, duplicates inflate KPIs, or late events make windowed outputs confusing.

**Rising action:** You diagnose systematically:
- Reproduce the issue with a controlled generator config (seeded run / smaller throughput).
- Inspect one “bad” event end-to-end (JSON → AVRO → consumer decode) and identify whether it’s schema mismatch, missing fields, invalid enums, or timestamp issues.
- Adjust generator logic so edge cases are intentional and explainable (e.g., duplicates flagged by IDs, out-of-order bounded by distributions), not random chaos.

**Climax:** You hit the key lesson: streaming correctness isn’t optional—late/out-of-order/duplicates must be designed, not just observed. You make the generator produce “teachable failures” that later prove watermarks and event-time choices.

**Resolution:** The generator produces realistic streams that are stable enough to build on, but rich enough that the analytics will visibly change in real time and reveal meaningful anomalies.

### Journey 3 — Professor/Grader (Evaluator + Operator) Milestone 1 review

**Opening scene:** The professor pulls your private repo and reads the README/design note to understand the two feeds, why they exist, and what analytics they enable.

**Rising action:** They inspect schemas and samples:
- Validate that AVRO schemas are sensible (types/enums/optionals) and include event-time + join IDs.
- Verify you can produce JSON and AVRO samples and that your documentation explains assumptions and edge cases clearly.

**Climax:** They look for the “streaming correctness setup”: does your data actually include late events, duplicates, missing steps, impossible durations, and courier offline scenarios—clearly described and justifiable?

**Resolution:** They provide feedback that you can immediately translate into Milestone 2 processing requirements (what to watermark, which windows matter, which joins are needed).

### Journey 4 — Professor/Grader (Evaluator + Operator) Milestone 2 demo (live insights)

**Opening scene:** During the demo, the professor runs/observes the full pipeline: Event Hubs ingestion → Spark Structured Streaming processing → Parquet outputs → live dashboard.

**Rising action:** They check rubric-aligned evidence:
- You document topic/partition/key strategy and expected throughput.
- Spark jobs show event-time processing with watermarks and windowing.
- Outputs include Parquet at rest plus aggregated metrics.

**Climax:** The dashboard “feels live”: metrics and graphs update continuously and correctly (typical < 15s freshness), and the visuals support at least one basic, one intermediate (state/session), and one advanced (anomaly/fraud/forecasting) use case.

**Resolution:** The professor can infer real-time operation from observable changes and the documented architecture, and can grade your learning outcomes and tradeoff reflection.

### Journey Requirements Summary

- Reproducible run experience: clear “how to run” commands, config defaults, and a predictable demo path.
- Debuggability: clear logging, simple health checks, and the ability to run smaller/faster “debug mode” configs.
- Schema discipline: AVRO schemas + validation and a documented evolution approach.
- Edge-case control: configurable toggles for late/out-of-order/duplicates/missing steps/impossible durations so behaviors are demonstrable.
- Live analytics readiness: event-time fields and join IDs that enable windows/watermarks/stateful logic.
- Dashboard usability: multiple real-time KPIs/graphs, filters (zone/restaurant), and at least one “health/anomaly” view.

## Domain-Specific Requirements

### Compliance & Regulatory

- No real compliance scope (educational simulation). The system will not process real customer data.
- All entities use anonymous identifiers only (no names, emails, phone numbers, or addresses).

### Technical Constraints

- No authentication required for the dashboard (trusted demo / course environment).
- System operation should be driven from the GUI: a user can start/stop (or at minimum control) the demo run and see live metrics without needing to run multiple manual CLI steps.
- Real-time freshness target remains: typical end-to-end dashboard update lag < 15s (defined in Success Criteria).

### Integration Requirements

- UI controls trigger or orchestrate the underlying pipeline runs (generator and/or streaming job lifecycle), even if the underlying components remain separate.

### Risk Mitigations

- Avoid PII-like fields in generated events to prevent accidental “real data” interpretation.
- Minimize demo friction by making the GUI the primary entry point (clear status indicators and predictable run flow).

## Data/Analytics Backend with Dashboard – Specific Requirements

### Project-Type Overview

- The system is a Python-based real-time analytics backend with a **Streamlit** dashboard on top of Spark-processed streaming data.
- The primary goal is to demonstrate end-to-end real-time analytics for a synthetic food-delivery platform, not to build production-grade observability tooling.
- A **full local demo mode** must be controllable from the Streamlit GUI.

### Technical Architecture Considerations

- **Dashboard platform:** Streamlit is the primary dashboard framework.
- **Demo orchestration from GUI:**
  - Streamlit app provides controls to start/stop (or trigger) a local “demo run” that:
    - Starts or configures the generator in demo mode.
    - Connects to Spark-processed aggregated outputs suitable for live visualization.
  - CLI-only workflows should not be required for a standard demo; advanced scripts are optional.
- **Data source for dashboard:**
  - Dashboard reads **aggregated outputs produced by Spark Structured Streaming**, not raw event streams.
  - Aggregates are designed to support the required basic/intermediate/advanced use cases and the filters below.

### Implementation Considerations

- **Filters (minimum set):**
  - Zone
  - Restaurant
  - Time window (e.g., last 15 minutes / 1 hour / 24 hours)
- **Filters (nice-to-have extras, if time permits):**
  - Courier
  - Order status (active / completed / cancelled)
  - Anomaly flag (e.g., anomalous deliveries, stressed zones)
- **UI behavior:**
  - Changing filters should update KPIs and charts quickly (within the < 15s freshness budget for underlying data).
  - The Streamlit app should make it obvious which filters are active (no ambiguity about the current slice of data).

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Demonstrate the full set of course learning outcomes with a clean, working end-to-end pipeline, while slightly pushing on the technical side (robust edge cases, at least one well-implemented advanced use case, and a clear Streamlit dashboard), rather than building heavy production infra.

**Resource Requirements:** Solo developer, time-boxed around Milestone 1 and Milestone 2 deadlines, prioritizing correctness and clarity over breadth of features.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Student/Developer builds, debugs, and runs the generator and pipeline end-to-end, and can see realistic, edge-case-rich data flowing.
- Professor/Grader can clone the repo, follow the README, run a guided demo, and observe live metrics and analytics on the dashboard.

**Must-Have Capabilities:**
- Two AVRO-modeled feeds with JSON + AVRO event generation, realistic distributions, and clearly documented edge cases (late/out-of-order/duplicates/missing steps/impossible durations/courier offline).
- Event Hubs ingestion with documented topic/partition/key strategy.
- Spark Structured Streaming jobs implementing parsing/validation/enrichment, event-time processing, watermarks, and appropriate windowing.
- Parquet outputs in Azure Blob Storage plus aggregated metrics ready for dashboard consumption.
- Streamlit dashboard that:
  - Shows key KPIs and time-series views.
  - Supports filters for zone, restaurant, and time window.
  - Includes at least one anomaly/health view aligned with the advanced use case.
- Required documentation and reflection summary per the course rubric.

### Post-MVP Features

**Phase 2 (Post-MVP / Stretch):**
- Additional filters (courier, order status, anomaly flags) and richer drilldowns.
- Extra derived metrics beyond the rubric minimums.
- Optional integration with tools like Grafana/Kibana for a subset of metrics if time allows.

**Phase 3 (Expansion / Vision):**
- Production-hardening of the pipeline (stronger reliability, scaling, backpressure, replayability).
- Governance and data management improvements (schema registry, contracts, lineage).
- More advanced analytics (forecasting, causal analysis, robust fraud detection, experimentation support).

### Risk Mitigation Strategy

**Technical Risks:** Focus early on getting the generator, schemas, and one end-to-end Spark/Streamlit slice working; treat extra metrics and integrations as optional layers rather than core dependencies.

**Market/Educational Risks:** Align closely with the rubric and examples discussed in class so the project clearly demonstrates the targeted concepts (watermarks, windows, anomaly detection) without over-focusing on tooling choices.

**Resource Risks:** If time runs short, defer Phase 2/3 items and prioritize a stable, well-documented MVP that is easy to run and grade.

## Functional Requirements

### Data Generation & Feeds

- FR1: The Student/Developer can configure and run a feed generator that produces two distinct event streams representing core food-delivery operations.
- FR2: The Student/Developer can define and update AVRO schemas for each feed without changing generator code structure.
- FR3: The Student/Developer can generate events in both JSON and AVRO formats for each feed.
- FR4: The Student/Developer can configure generator parameters such as number of restaurants, couriers, zones, and demand levels.
- FR5: The Student/Developer can enable or disable specific edge-case behaviors (late events, duplicates, missing steps, impossible durations, courier offline) via configuration.
- FR6: The Student/Developer can produce small sample batches of events for inspection and debugging.

### Streaming Ingestion

- FR7: The Student/Developer can configure the generator to publish events to Azure Event Hubs.
- FR8: The Student/Developer can specify Event Hubs connection settings (namespace, hub name, authentication parameters) via configuration files or environment.
- FR9: The Student/Developer can define and adjust topic/partition/keying strategy for each feed.
- FR10: The Professor/Grader can view documentation that explains the chosen topic/partition/key strategy and expected throughput.

### Stream Processing & Storage

- FR11: The Student/Developer can configure and run Spark Structured Streaming jobs that consume the two feeds from Event Hubs.
- FR12: The Student/Developer can define parsing and validation rules for incoming events, so that invalid records are routed to a dedicated error sink with a reason code while the streaming job continues running without failure.
- FR13: The Student/Developer can enrich events with derived fields or reference data needed for analytics.
- FR14: The Student/Developer can configure event-time semantics and watermarks for each stream.
- FR15: The Student/Developer can define at least one basic windowed KPI computation over the event streams.
- FR16: The Student/Developer can define at least one intermediate stateful or session-based metric over the event streams.
- FR17: The Student/Developer can define at least one advanced anomaly or fraud-style metric that uses recent history and/or late data handling.
- FR18: The Student/Developer can write curated outputs from Spark Structured Streaming into Parquet files on Azure Blob Storage.
- FR19: The Professor/Grader can inspect the Parquet outputs to confirm that they match the documented schemas and metric definitions.

### Analytics Dashboard & Insights

- FR20: The Student/Developer can run a Streamlit application that connects to the aggregated outputs produced by Spark.
- FR21: The Dashboard Viewer can see, on the Streamlit dashboard, at minimum the following KPIs updated on each refresh: total active orders, average delivery time over the last configured time window, and cancellation rate over the last configured time window.
- FR22: The Dashboard Viewer can view at least one time-series chart that shows how metrics evolve over time.
- FR23: The Dashboard Viewer can filter metrics and charts by zone.
- FR24: The Dashboard Viewer can filter metrics and charts by restaurant.
- FR25: The Dashboard Viewer can select a time window (for example last 15 minutes, 1 hour, or 24 hours) for displayed data.
- FR26: The Dashboard Viewer can see a health/anomaly-oriented view that highlights, for each time window, the top N zones (configurable, default N ≤ 10) whose delivery-time anomaly score or stress index exceeds a configured threshold.
- FR27: The Dashboard Viewer can identify which filters are currently active in the dashboard UI.

### Demo Orchestration & Operations

- FR28: The Student/Developer can start a local demo mode from the Streamlit UI that triggers or guides generator and pipeline execution.
- FR29: The Student/Developer can stop or reset the demo mode from the Streamlit UI without manually terminating multiple CLI processes.
- FR30: The Student/Developer can see in the UI (a) generator status (Running/Stopped/Error), (b) streaming job status (Running/Stopped/Error), and (c) the timestamp of the last successfully processed batch, all updated at least every 10 seconds while the demo is running.
- FR31: The Professor/Grader can follow documented steps to reproduce a typical demo run without modifying code.

### Observability, Debugging & Edge Cases

- FR32: The Student/Developer can run the generator in a “debug mode” that limits throughput to a configurable maximum (for example ≤ 100 events per second) and caps entity counts (for example ≤ 20 restaurants and ≤ 20 couriers), so that a target scenario can be reproduced end-to-end in under 60 seconds using a documented config flag (for example `mode=debug`).
- FR33: The Student/Developer can inspect example events and schemas to understand how edge cases are encoded.
- FR34: The Student/Developer can verify, through the dashboard or logs, that late/out-of-order events are being processed according to the configured watermarks.
- FR35: The Student/Developer can verify, through metrics or sample queries, that duplicates and missing-step sequences are handled in a known, documented way.

### Documentation & Reflection

- FR36: The Student/Developer can produce a README that explains how to run the generator, pipeline, and dashboard for both sample and full demos.
- FR37: The Student/Developer can maintain a design note that describes feed schemas, assumptions, and how they support the planned analytics.
- FR38: The Student/Developer can document the implemented basic, intermediate, and advanced use cases and how they appear in the dashboard.
- FR39: The Student/Developer can produce a short reflection document that explains key tradeoffs, limitations, and what would be needed for production readiness.

## Non-Functional Requirements

### Performance

- NFR1: Under typical demo conditions, the 95th-percentile end-to-end latency from event generation to updated dashboard metrics should be less than 15 seconds, as measured over at least a 5-minute demo run using wall-clock timestamps between generator emit and dashboard refresh.
- NFR2: Under typical demo conditions for a single viewer on course-standard hardware, 90% of dashboard filter interactions (changing zone, restaurant, or time window) should complete with updated charts within 3 seconds, as measured from user action to visible update in a screen recording or log trace.

### Security

- NFR3: The system must not process real customer data; all entities are represented with anonymous identifiers and synthetic attributes, and schemas and sample events must not contain names, emails, phone numbers, or real-world addresses, as verified by schema review and spot-checks on generated data.
- NFR4: For the standard course deployment, authentication for the dashboard is not required; the dashboard must be reachable on localhost or a controlled lab network without a login step, as confirmed by running the documented demo flow.

### Operability & Setup

- NFR5: A new user familiar with the course environment should be able to set up and run the full demo in 45 minutes or less by following the provided README and design note, without needing to read source code, as validated by at least one fresh-user setup test.
- NFR6: Under a documented “typical demo” load range (for example event rates and volumes defined in the README), the demo run path should complete without unhandled errors and without streaming job failure, with any invalid records handled via the error sink defined in FR12; this should be demonstrated in at least one full demo run without manual intervention.
