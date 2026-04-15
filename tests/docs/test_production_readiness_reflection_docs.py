from __future__ import annotations

from pathlib import Path


def test_production_readiness_reflection_exists_with_required_sections():
    root = Path(__file__).resolve().parents[2]
    reflection_path = root / "docs" / "production_readiness_reflection.md"
    assert reflection_path.exists()

    reflection = reflection_path.read_text(encoding="utf-8")
    assert "Tradeoffs in the Current Implementation" in reflection
    assert "Known Limitations in the Demo Scope" in reflection
    assert "Production-Readiness Action Plan" in reflection
    assert "NFR1" in reflection
    assert "NFR6" in reflection
    assert "stream_analytics/dashboard/app.py" in reflection
    assert "stream_analytics/orchestration/demo_runner.py" in reflection
    # AC-level checks: tradeoffs, limitations, and concrete production actions.
    assert "Responsiveness vs analytical flexibility" in reflection
    assert "Demo control simplicity vs orchestration robustness" in reflection
    assert "Lightweight observability vs deep production telemetry" in reflection
    assert "Synthetic-only data model" in reflection
    assert "single-team demo operation" in reflection
    assert "Reliability hardening" in reflection
    assert "Scalability and performance" in reflection
    assert "Governance and security" in reflection


def test_readme_links_to_production_readiness_reflection():
    root = Path(__file__).resolve().parents[2]
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    assert "Production Readiness Reflection (Story 6.2)" in readme
    assert "docs/production_readiness_reflection.md" in readme
