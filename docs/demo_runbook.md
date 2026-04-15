# Demo Runbook (Story 5.3)

This runbook is the official reproducible demo path for graders.

Standard objective: start the demo, verify live status updates (`RUNNING` and `last_batch_ts`), then stop/reset cleanly without editing any source files.

## Scope and Guarantees

- Uses the existing dashboard lifecycle controls from Story 5.1: `Start Demo`, `Stop Demo`, `Reset Demo`.
- Uses the existing status semantics from Story 5.2: `RUNNING` / `STOPPED` / `ERROR`, heartbeat, and `last_batch_ts`.
- Uses only configuration and commands already present in this repository.
- No source-code edits are required for the standard run.

## Prerequisites Checklist

- [ ] Python 3.10+ is installed.
- [ ] Dependencies are installed from `requirements.txt`.
- [ ] Azure Event Hubs credentials are set:
  - `EVENTHUB_CONNECTION_STRING`
  - `SPARK_EVENTHUB_CONNECTION_STRING`
- [ ] Working folders exist (or are created): `status/`, `logs/`, and output/checkpoint paths used by config.
- [ ] `config/dashboard.yaml` includes non-empty `generator_command` and `spark_command`.

## 1) Setup

### Windows PowerShell (primary)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux/macOS alternative

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2) Environment Variables (PowerShell)

Set these before running the dashboard and demo controls:

```powershell
$env:EVENTHUB_CONNECTION_STRING="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
$env:SPARK_EVENTHUB_CONNECTION_STRING="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
```

Optional Event Hub name overrides:

```powershell
$env:GENERATOR_EVENT_HUBS_ORDER_TOPIC="order-events"
$env:GENERATOR_EVENT_HUBS_COURIER_TOPIC="courier-status"
$env:SPARK_JOBS_ORDER_EVENT_HUB_NAME="order-events"
$env:SPARK_JOBS_COURIER_EVENT_HUB_NAME="courier-status"
```

## 3) Preflight Validation (copy-paste)

### Windows PowerShell (primary)

```powershell
python --version
pip --version
python -m pytest tests/dashboard/test_demo_controls.py tests/dashboard/test_status_display.py tests/orchestration/test_demo_runner.py
Test-Path "config/dashboard.yaml"
Test-Path "stream_analytics/dashboard/app.py"
New-Item -ItemType Directory -Force status, logs | Out-Null
Test-Path "status"
Test-Path "logs"
```

### Linux/macOS alternative

```bash
python --version
pip --version
python -m pytest tests/dashboard/test_demo_controls.py tests/dashboard/test_status_display.py tests/orchestration/test_demo_runner.py
test -f "config/dashboard.yaml"
test -f "stream_analytics/dashboard/app.py"
mkdir -p status logs
test -d "status"
test -d "logs"
```

Expected preflight outcomes:

- Pytest command passes.
- All `Test-Path` checks return `True`.
- `status/` and `logs/` exist.

## 4) Start Dashboard

### Windows PowerShell (primary)

```powershell
streamlit run stream_analytics/dashboard/app.py
```

### Linux/macOS alternative

```bash
streamlit run stream_analytics/dashboard/app.py
```

## 5) Reproducible Demo Lifecycle

In the dashboard:

1. Open `Demo Lifecycle` controls.
2. Click `Start Demo`.
3. Watch `Pipeline Status`.
4. Optionally open `Debug / Status` page while auto-refresh is enabled.
5. Click `Stop Demo` (or `Reset Demo` for hard reset).

### Expected checkpoints after `Start Demo`

- `Demo run state` shows `RUNNING`.
- `Generator` metric shows `RUNNING`.
- `Spark Streaming` metric shows `RUNNING`.
- `Last Processed Batch` transitions from `Waiting for first batch` to a timestamp.
- `Batch Age` refreshes on each auto-refresh cycle and should stay near the dashboard refresh cadence (default 15 seconds, acceptable around 10-15 seconds).
- Status artifacts exist and update:
  - `status/generator_status.json`
  - `status/spark_job_status.json`

## 6) Healthy vs Stalled/Error Signals

### Healthy demo signals

- Both process states remain `RUNNING`.
- `last_batch_ts` updates regularly (or has a heartbeat approximation message while data starts flowing).
- `message` fields remain informational (no startup/termination failures).

### Stalled or error signals

- `Spark Streaming` or `Generator` shows `ERROR`.
- Spark status `message` includes startup/runtime failures or missing config hints.
- `Last Processed Batch` remains `Waiting for first batch` for an extended period while upstream should be active.
- `last_batch_ts` has the heartbeat-approximation note for too long without real data evidence from logs/Event Hubs.
- Status JSON `message` indicates startup failure, missing config, or status file corruption.

## 7) Stop, Reset, and Post-Run Verification

Use dashboard buttons:

- `Stop Demo`: graceful stop while preserving a stop timestamp.
- `Reset Demo`: stop + reset batch timestamp state for a clean next run.

Post-run verification checks (PowerShell):

```powershell
Get-ChildItem status
Get-Content status\generator_status.json
Get-Content status\spark_job_status.json
```

Linux/macOS alternative:

```bash
ls status
cat status/generator_status.json
cat status/spark_job_status.json
```

Expected terminal state after stop/reset:

- No orphaned managed processes remain.
- Status files report `STOPPED`.
- PID files are cleaned up by orchestration (`status/generator.pid`, `status/spark.pid` removed).

## 8) Troubleshooting (reproducible recovery)

| Symptom | What to check | Recovery |
| --- | --- | --- |
| Missing Azure config / auth failures | `EVENTHUB_CONNECTION_STRING`, `SPARK_EVENTHUB_CONNECTION_STRING` | Set/correct env vars, then click `Reset Demo` and `Start Demo` |
| Stale `last_batch_ts` / rising batch age | `status/spark_job_status.json` `message`, Event Hubs flow | Wait for first batch if initial startup; otherwise `Reset Demo` |
| Missing or corrupt status file | `status/generator_status.json`, `status/spark_job_status.json` readability | Delete corrupt file and use `Reset Demo`; dashboard recreates safe defaults |
| Spark not reachable / start failure | dashboard run-state message and status `message` | Verify `spark_command` in `config/dashboard.yaml`, then full restart |

When to use controls:

- Use `Reset Demo` first for stale state, stale PID artifacts, or status-file drift.
- Use full restart (close dashboard + rerun command) if repeated `ERROR` persists after reset.

## 9) Log and Artifact Inspection

Inspect these artifacts for diagnostics:

- `status/generator_status.json`
- `status/spark_job_status.json`
- `logs/*.log` (if generated by your local run configuration)

PowerShell helpers:

```powershell
Get-Content status\generator_status.json
Get-Content status\spark_job_status.json
Get-ChildItem logs
```

Linux/macOS helpers:

```bash
cat status/generator_status.json
cat status/spark_job_status.json
ls logs
```

## 10) Standard Demo Completion Criteria

The demo run is considered reproducible and successful when:

1. Setup/preflight pass with no code edits.
2. `Start Demo` moves both processes to `RUNNING`.
3. `last_batch_ts` appears and batch-age behavior is consistent with refresh cadence.
4. `Stop Demo` or `Reset Demo` returns system to clean `STOPPED` state.
