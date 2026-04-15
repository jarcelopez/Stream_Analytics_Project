from __future__ import annotations

from pathlib import Path


def test_demo_runbook_exists_and_references_core_artifacts():
    root = Path(__file__).resolve().parents[2]
    runbook_path = root / "docs" / "demo_runbook.md"
    assert runbook_path.exists()

    runbook = runbook_path.read_text(encoding="utf-8")
    assert "status/generator_status.json" in runbook
    assert "status/spark_job_status.json" in runbook
    assert "streamlit run stream_analytics/dashboard/app.py" in runbook
    assert "Reset Demo" in runbook
    assert "Healthy demo signals" in runbook
    assert "Stalled or error signals" in runbook
    assert "Troubleshooting (reproducible recovery)" in runbook
    assert "No source-code edits are required for the standard run." in runbook
    assert "### Linux/macOS alternative" in runbook


def test_readme_links_to_demo_runbook_and_control_flow():
    root = Path(__file__).resolve().parents[2]
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    assert "docs/demo_runbook.md" in readme
    assert "Start Demo" in readme
    assert "Stop Demo" in readme
    assert "Reset Demo" in readme
    assert "Quick command path (PowerShell)" in readme
    assert "Quick command path (Linux/macOS)" in readme
