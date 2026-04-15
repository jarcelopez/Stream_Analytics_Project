# Production Readiness Reflection (Story 6.2)

This reflection summarizes the key tradeoffs made for an educational streaming demo and what must change to move toward production-grade operation.

## Tradeoffs in the Current Implementation

### 1) Responsiveness vs analytical flexibility

- The dashboard prioritizes quick interactions by reading a curated denormalized metrics dataset (`data/metrics_by_zone_restaurant_window`) rather than computing heavy aggregations in the UI.
- This design targets the responsiveness goals in `NFR1` and `NFR2` for typical demo usage, but it limits ad-hoc slicing dimensions unless Spark jobs are extended first.
- Evidence:
  - `stream_analytics/dashboard/app.py` reads precomputed parquet and applies lightweight filters.
  - `stream_analytics/spark_jobs/windowed_kpis.py` and `stream_analytics/spark_jobs/anomaly_scores.py` materialize the KPI/anomaly shape consumed by the dashboard.

### 2) Demo control simplicity vs orchestration robustness

- A single Streamlit entry point (`Start Demo`, `Stop Demo`, `Reset Demo`) reduces setup friction and helps satisfy `NFR5` (new-user reproducibility).
- The same choice intentionally avoids a separate scheduler/supervisor service and keeps process lifecycle control lightweight.
- Evidence:
  - `stream_analytics/dashboard/app.py` invokes orchestration controls directly.
  - `stream_analytics/orchestration/demo_runner.py` manages child processes and status files with idempotent start/stop semantics.

### 3) Lightweight observability vs deep production telemetry

- The project uses file-based status artifacts and structured status messages (`status/generator_status.json`, `status/spark_job_status.json`) that are easy for graders to inspect.
- This is effective for course demos and aligns with reproducible runbook behavior, but it does not provide full production observability (distributed traces, centralized metrics/alerts, SLO tracking).
- Evidence:
  - `docs/demo_runbook.md` documents healthy/stalled signals from status files.
  - `stream_analytics/orchestration/status_files.py` and `stream_analytics/orchestration/demo_runner.py` define status persistence and heartbeat behavior.

### 4) Event-time correctness vs operational tuning burden

- Spark watermark/window processing improves correctness under late/out-of-order records and supports `NFR6` resilience expectations for typical loads.
- The tradeoff is operational sensitivity: watermark/window thresholds must be tuned carefully to balance state growth, latency, and late-data loss risk.
- Evidence:
  - `config/spark_jobs.yaml` watermark/window settings.
  - `stream_analytics/spark_jobs/windowing.py` and `stream_analytics/spark_jobs/ingestion.py` event-time and validation pipeline behavior.

## Known Limitations in the Demo Scope

- Synthetic-only data model (`NFR3`) and trusted local/lab access assumptions (`NFR4`) mean security and privacy controls are intentionally minimal for MVP.
- The system is optimized for single-team demo operation, not concurrent multi-tenant usage or high-throughput autoscaling.
- Process orchestration is local and file-backed; failures are visible but not automatically remediated by a hardened supervisor.
- Dashboard health ranking relies on curated metric availability and configured thresholds; poor tuning can degrade relevance.
- The current observability model is strong for manual grading, but weak for large-scale incident detection and on-call operations.

## Production-Readiness Action Plan

### Reliability hardening

1. Introduce supervised orchestration (service manager/workload scheduler) with restart policies and bounded backoff.
2. Formalize replay and recovery procedures for Event Hubs and Spark checkpoints.
3. Strengthen idempotency and duplicate-control contracts across ingestion and downstream sinks.

### Scalability and performance

1. Run repeatable load tests against documented event-rate envelopes and latency targets.
2. Tune watermark/state-store strategy using measured state size, late-data ratios, and end-to-end latency.
3. Validate partitioning/autoscaling behavior for Event Hubs throughput and Spark micro-batch stability.

### Governance and security

1. Add stronger access controls (dashboard authn/authz beyond trusted local usage).
2. Formalize schema/contract governance (versioning policy, compatibility checks, producer-consumer contract tests).
3. Expand lineage and auditability around curated outputs and pipeline transitions.
4. Define data quality SLOs/SLAs with automated checks and alerting.

## Traceability References

- PRD requirements: `_bmad-output/planning-artifacts/prd.md` (`FR39`, `NFR1`..`NFR6`)
- Dashboard behavior: `stream_analytics/dashboard/app.py`
- Demo orchestration and status: `stream_analytics/orchestration/demo_runner.py`, `stream_analytics/orchestration/status_files.py`
- Spark processing path: `stream_analytics/spark_jobs/ingestion.py`, `stream_analytics/spark_jobs/windowing.py`, `stream_analytics/spark_jobs/windowed_kpis.py`, `stream_analytics/spark_jobs/anomaly_scores.py`
- Run/verification workflow: `docs/demo_runbook.md`
