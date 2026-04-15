from __future__ import annotations

from datetime import UTC, datetime

from stream_analytics.dashboard.app import (
    _build_demo_controls_state,
    _format_last_batch_display,
    _show_run_state_message,
    _status_badge_text,
)


def test_build_demo_controls_state_for_running():
    controls = _build_demo_controls_state("RUNNING")
    assert controls["start_disabled"] is True
    assert controls["stop_disabled"] is False


def test_build_demo_controls_state_for_stopped():
    controls = _build_demo_controls_state("STOPPED")
    assert controls["start_disabled"] is False
    assert controls["stop_disabled"] is True


def test_show_run_state_message_routes_to_error_channel():
    class _FakeStreamlit:
        def __init__(self):
            self.errors = []
            self.infos = []
            self.successes = []

        def success(self, message):
            self.successes.append(message)

        def info(self, message):
            self.infos.append(message)

        def error(self, message):
            self.errors.append(message)

    st = _FakeStreamlit()
    _show_run_state_message(st=st, run_state="ERROR", message="boom")
    assert st.errors == ["boom"]


def test_status_badge_text_supports_expected_states():
    assert _status_badge_text("RUNNING") == "RUNNING"
    assert _status_badge_text("ERROR") == "ERROR"
    assert _status_badge_text("stopped") == "STOPPED"


def test_format_last_batch_display_with_valid_timestamp():
    batch_value, batch_age = _format_last_batch_display(
        "2026-04-15T10:00:00+00:00",
        now_utc=datetime(2026, 4, 15, 10, 0, 20, tzinfo=UTC),
    )
    assert "2026-04-15 10:00:00 UTC" in batch_value
    assert batch_age == "20s ago"


def test_format_last_batch_display_handles_missing_timestamp():
    batch_value, batch_age = _format_last_batch_display(None)
    assert batch_value == "Waiting for first batch"
    assert batch_age == "n/a"
