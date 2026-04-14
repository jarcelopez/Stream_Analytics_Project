from __future__ import annotations

from types import SimpleNamespace

import pytest

from stream_analytics.publisher import event_hub_publisher as publisher


def test_partition_key_strategy_uses_zone_for_orders_and_courier_for_courier_feed():
    order_event = {"zone_id": "zone-2", "courier_id": "courier-11"}
    courier_event = {"zone_id": "zone-3", "courier_id": "courier-42"}

    assert publisher._event_partition_key(order_event, "order_events") == "zone-2"
    assert publisher._event_partition_key(courier_event, "courier_status") == "courier-42"


def test_partition_key_strategy_independent_of_custom_hub_names(monkeypatch):
    captured_partition_keys = []

    class FakeBatch:
        def __init__(self) -> None:
            self.count = 0

        def add(self, payload) -> None:
            self.count += 1

        def __len__(self) -> int:
            return self.count

    class FakeProducer:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def create_batch(self, partition_key=None):
            captured_partition_keys.append(partition_key)
            return FakeBatch()

        def send_batch(self, batch) -> None:
            return None

    cfg = SimpleNamespace(
        zone_count=1,
        restaurant_count=1,
        courier_count=1,
        sample_batch_size_per_feed=1,
    )

    monkeypatch.setattr(
        publisher,
        "generate_two_feeds_sample",
        lambda **kwargs: (
            [{"zone_id": "zone-99", "courier_id": "courier-1"}],
            [{"zone_id": "zone-88", "courier_id": "courier-9"}],
        ),
    )
    monkeypatch.setattr(publisher, "_build_producer", lambda *args, **kwargs: FakeProducer())

    publisher.publish_once(
        cfg,  # type: ignore[arg-type]
        "Endpoint=sb://ns.servicebus.windows.net/;SharedAccessKeyName=n;SharedAccessKey=k",
        "custom-order-hub",
        "custom-courier-hub",
        dry_run=False,
    )

    assert captured_partition_keys[0] == "zone-99"
    assert captured_partition_keys[1] == "courier-9"


def test_resolve_hub_name_fails_fast_on_empty_value():
    with pytest.raises(SystemExit):
        publisher._resolve_hub_name("   ", "", "event_hubs_order_topic")


def test_send_feed_retries_batch_send(monkeypatch):
    class FakeBatch:
        def __init__(self) -> None:
            self.count = 0

        def add(self, payload) -> None:
            self.count += 1

        def __len__(self) -> int:
            return self.count

    class FakeProducer:
        def __init__(self) -> None:
            self.send_attempts = 0

        def create_batch(self, partition_key=None):
            return FakeBatch()

        def send_batch(self, batch) -> None:
            self.send_attempts += 1
            if self.send_attempts == 1:
                raise RuntimeError("transient failure")

    monkeypatch.setattr(publisher, "EventHubError", RuntimeError)
    monkeypatch.setattr(publisher.time, "sleep", lambda _: None)

    producer = FakeProducer()
    sent = publisher._send_feed(
        producer,  # type: ignore[arg-type]
        [{"zone_id": "zone-1", "courier_id": "courier-1"}],
        "order-events",
        "order_events",
        dry_run=False,
    )

    assert sent == 1
    assert producer.send_attempts == 2


def test_main_uses_generator_underscore_env_prefix(monkeypatch):
    cfg = SimpleNamespace(
        event_hubs_order_topic=None,
        event_hubs_courier_topic=None,
    )
    captured = {}

    def fake_load_typed_config(*, relative_yaml_path, model_type, env_prefix):
        captured["env_prefix"] = env_prefix
        return cfg

    monkeypatch.setattr(publisher, "load_typed_config", fake_load_typed_config)
    monkeypatch.setattr(publisher, "run_batch", lambda *args, **kwargs: None)

    publisher.main(["--batch", "--dry-run"])

    assert captured["env_prefix"] == "GENERATOR_"
