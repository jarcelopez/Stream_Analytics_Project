from __future__ import annotations

from stream_analytics.dashboard.app import _build_demo_controls_state, _show_run_state_message


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
