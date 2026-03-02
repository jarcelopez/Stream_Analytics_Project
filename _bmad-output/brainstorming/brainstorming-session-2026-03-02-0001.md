---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Design and implementation of a Python-based real-time analytics pipeline for a synthetic food-delivery platform across two milestones'
session_goals: 'Plan and structure Milestone 1 (due in 1 week, solo) so that the streaming feeds, schemas, and edge cases are well-designed to unlock Milestone 2 analytics and dashboard.'
selected_approach: 'progressive-flow'
techniques_used: []
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** {{user_name}}
**Date:** {{date}}

## Session Overview

**Topic:** Design and implementation of a Python-based real-time analytics pipeline for a synthetic food-delivery platform, implemented entirely in Python, structured into two course milestones.

**Goals:** 
- Clarify and prioritize analytics use cases and metrics that matter most for the course and for demonstrating streaming concepts.
- Shape the two streaming feeds, schemas, and edge cases in Milestone 1 so that Milestone 2 processing (Spark Structured Streaming, windows, watermarks, anomalies, KPIs) is natural and well-supported.
- Turn this into a realistic, week-long solo plan for Milestone 1, with a clear view of how it connects to Milestone 2.

### Context Guidance

_No additional external context file was provided; session is grounded on the course assignment requirements and your Python-only, solo, one-week constraint for Milestone 1._

### Session Setup

This session focuses on designing the project so that:
- Milestone 1 produces realistic, configurable, and analytically rich event streams (with AVRO schemas, JSON/AVRO generation, and edge cases).
- These streams directly support Milestone 2 ingestion into Azure Event Hubs, Spark Structured Streaming processing, Parquet storage, and a live dashboard.
- The work is broken down into manageable tasks for a single developer within one week for Milestone 1.

## Technique Selection

**Approach:** Progressive Technique Flow  
**Journey Design:** Systematic development from exploration to action

**Progressive Techniques:**

- **Phase 1 – Exploration:** What If Scenarios (explore KPIs around volume, speed, and customer experience; Delivery Time Anomaly Score; Zone Stress Index).
- **Phase 2 – Pattern Recognition:** Mind Mapping (cluster ideas into feeds/schemas, analytics/use-cases, edge cases, infra, and dashboard views).
- **Phase 3 – Development:** Morphological Analysis (combine choices of entities, fields, and edge-case behaviours to converge on two concrete feeds and schemas).
- **Phase 4 – Action Planning:** Decision Tree Mapping (turn design into a milestone plan, package structure, and config options).

**Journey Rationale:** This flow starts by exploring what you want to measure (volume, speed, CX), then shapes feed and schema design to support those metrics, and finally turns everything into a concrete solo-implementable plan for Milestone 1 that cleanly hands off into Milestone 2.

## Key Design Decisions

### Epics and Milestones

- **Epic 1 – Streaming Feed Design & Generator (Milestone 1)**
  - Define two feeds that support Delivery Time Anomaly Score and Zone Stress Index.
  - Design and version AVRO schemas for both feeds.
  - Implement a Python generator that emits JSON and AVRO with realistic distributions and configurable parameters.
  - Inject streaming edge cases (late events, duplicates, missing steps, impossible durations, couriers going offline).
  - Provide sample batches and documentation (README + design note).

- **Epic 2 – Stream Processing & Storage (Milestone 2, Part 1)**
  - Ingest both feeds into Azure Event Hubs with a documented topic/partition/key strategy.
  - Implement Spark Structured Streaming jobs (parsing, validation, enrichment, event-time, watermarks, windows).
  - Persist curated data at rest in Parquet on Azure Blob Storage.

- **Epic 3 – Analytics, Metrics & Dashboard (Milestone 2, Part 2)**
  - Implement Delivery Time Anomaly Score per zone and Zone Stress Index as derived metrics.
  - Implement required basic/intermediate/advanced use cases using windowing and session/stateful logic.
  - Build a live Streamlit dashboard (or equivalent) with KPIs, filters, health view, and anomaly highlighting.
  - Write reflection on streaming tradeoffs and production-readiness gaps.

### Feed Definitions (Conceptual)

- **Feed A – Order Events**
  - Purpose: capture order-level economics and operational details needed for volume, revenue, and delivery-time analytics.
  - Core fields: `order_id`, `customer_id`, `seller_id`, `courier_id`, `zone_id`, `order_value`, `order_cost`, `commission`, `distance_to_delivery_point`, `delivery_method`, `event_type`, `event_time`, plus optional rating/cancellation fields for CX.

- **Feed B – Courier Status / Telemetry**
  - Purpose: capture courier-side capacity and reliability information for Zone Stress Index and session-based analytics.
  - Core fields: `courier_id`, `vehicle_type`, `energy_level` (battery/gas), `success_rate`, `estimated_eta`, `status`, `zone_id`, `event_time`.

### AVRO Schema Sketches (Finalised at Brainstorming Level)

- Both feeds use:
  - `string` identifiers for IDs (for simplicity in Spark and cross-tooling).
  - Logical timestamp fields (`event_time`) suitable for event-time processing.
  - Enums for status-like fields (e.g., `delivery_method`, `event_type`, `vehicle_type`, `status`).
  - Optional fields for customer ratings, cancellations, anomalies, etc., to support CX and anomaly analytics.

## Generator Package Structure (Planned)

Proposed Python package layout for Milestone 1:

- `stream_analytics_project/`
  - `__init__.py`
  - `config.py` – dataclasses / pydantic models for generator config and defaults.
  - `schemas/`
    - `order_events.avsc`
    - `courier_status.avsc`
  - `generator/`
    - `__init__.py`
    - `order_generator.py` – synthetic order event generation logic.
    - `courier_generator.py` – synthetic courier status/telemetry generation.
    - `distributions.py` – distributions for lunch/dinner peaks, weekday/weekend, zone skew.
    - `edge_cases.py` – utilities to inject late events, duplicates, missing steps, impossible durations, offline couriers.
    - `serialization.py` – JSON and AVRO serialization helpers.
    - `runner.py` – CLI/entrypoint to run generators with config.
  - `utils/`
    - `time_utils.py` – helper functions for timestamps, windows, and surges.
    - `ids.py` – ID generation helpers.
  - `samples/`
    - `json/` – small sample JSON batches.
    - `avro/` – small sample AVRO batches.

- Repository root support files:
  - `README.md` – project overview, how to run the generator, quickstart.
  - `docs/design-note-m1.md` – design note explaining feeds, schemas, assumptions, planned analytics.
  - `requirements.txt` – Python dependencies (e.g., `fastavro` or `avro-python3`, random/distribution libs).

## Generator Configuration (Planned Options & Defaults)

- **Global simulation config**
  - `simulation_duration_minutes` (default: 60)
  - `events_per_minute_base` (default: 200)
  - `time_granularity_seconds` (default: 1)

- **Entities**
  - `num_zones` (default: 8)
  - `num_restaurants` (default: 200)
  - `num_couriers` (default: 150)
  - `num_customers` (default: 5000)

- **Temporal patterns**
  - `lunch_peak_hour` (default: 13)
  - `dinner_peak_hour` (default: 20)
  - `weekday_multiplier` (default: 1.0)
  - `weekend_multiplier` (default: 1.3)
  - `zone_demand_multipliers` (default: dict with a few hot/cold zones)

- **Economics**
  - `avg_order_value` (default: 25.0)
  - `order_value_stddev` (default: 10.0)
  - `commission_rate` (default: 0.25)

- **Operational behaviour**
  - `base_prep_time_minutes` (default: 15)
  - `base_travel_time_minutes` (default: 20)
  - `courier_offline_probability` (default: 0.02 per hour)
  - `cancellation_probability` (default: 0.03)
  - `promo_periods` (default: empty list or simple example ranges)

- **Edge-case injection**
  - `late_event_fraction` (default: 0.05)
  - `duplicate_event_fraction` (default: 0.01)
  - `missing_step_fraction` (default: 0.01)
  - `impossible_duration_fraction` (default: 0.01)

- **Output**
  - `output_format` (choices: `json`, `avro`, `both`; default: `both`)
  - `output_path` (default: `samples/`)
  - `events_per_file` (default: 10_000)

## Milestone 1 README / Design Note Outline

- **1. Project Overview**
  - One-paragraph description of the streaming pipeline and course goals.
  - Brief note that Milestone 1 delivers synthetic feeds + generator; Milestone 2 will build processing and dashboard.

- **2. Feeds and Schemas**
  - Why two feeds (Order Events and Courier Status) are essential.
  - Which analytics they enable (Delivery Time Anomaly Score, Zone Stress Index, volume/speed/CX KPIs).
  - AVRO schema definitions and field-by-field explanation (including event-time and join keys).

- **3. Realism & Edge Cases**
  - Temporal patterns (lunch/dinner peaks, weekday/weekend).
  - Zone skew and entity cardinalities.
  - Edge cases: out-of-order events, duplicates, missing steps, impossible durations, couriers going offline.
  - How these support watermarks and event-time processing later.

- **4. Generator Design**
  - Package structure and key modules.
  - Overview of config system (what you can tune and why).
  - How JSON and AVRO outputs are produced.

- **5. How to Run**
  - Prerequisites (Python version, how to install requirements).
  - Example CLI commands to generate sample batches.
  - Location of sample data and schemas.

- **6. Planned Analytics (Preview of Milestone 2)**
  - Short description of Delivery Time Anomaly Score and Zone Stress Index.
  - How feed fields and edge cases directly support those analytics.

- **7. Assumptions and Limitations**
  - Simplifications made for the course.
  - Items deferred to Milestone 2 or out of scope.


