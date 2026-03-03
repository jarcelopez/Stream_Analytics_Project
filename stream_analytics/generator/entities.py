from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Iterator, List, Mapping, Tuple

from faker import Faker


fake = Faker()


@dataclass
class OrderEvent:
    order_id: str
    restaurant_id: str
    courier_id: str
    zone_id: str
    event_time: datetime
    status: str
    total_amount: float | None = None
    delivery_time_seconds: float | None = None

    def to_dict(self) -> Mapping:
        return {
            "order_id": self.order_id,
            "restaurant_id": self.restaurant_id,
            "courier_id": self.courier_id,
            "zone_id": self.zone_id,
            "event_time": int(self.event_time.timestamp() * 1_000_000),
            "status": self.status,
            "total_amount": self.total_amount,
            "delivery_time_seconds": self.delivery_time_seconds,
            "feed_type": "order_events",
        }


@dataclass
class CourierStatusEvent:
    courier_id: str
    zone_id: str
    event_time: datetime
    status: str
    active_order_id: str | None = None

    def to_dict(self) -> Mapping:
        return {
            "courier_id": self.courier_id,
            "zone_id": self.zone_id,
            "event_time": int(self.event_time.timestamp() * 1_000_000),
            "status": self.status,
            "active_order_id": self.active_order_id,
            "feed_type": "courier_status",
        }


def _now() -> datetime:
    return datetime.now(timezone.utc)


def seed_for_debug(seed: int = 0) -> None:
    """
    Seed the internal random generators used for sample data creation.

    This is intended for debug/demo runs where we want reproducible
    distributions given the same configuration.
    """
    fake.seed_instance(seed)


def generate_sample_orders(
    zone_count: int,
    restaurant_count: int,
    courier_count: int,
    sample_batch_size_per_feed: int,
) -> List[OrderEvent]:
    events: List[OrderEvent] = []
    for _ in range(sample_batch_size_per_feed):
        order_id = f"ord_{fake.uuid4()}"
        restaurant_id = f"rest_{fake.random_int(1, restaurant_count)}"
        courier_id = f"courier_{fake.random_int(1, courier_count)}"
        zone_id = f"zone_{fake.random_int(1, zone_count)}"
        status = fake.random_element(
            elements=("CREATED", "ACCEPTED", "ASSIGNED", "PICKED_UP", "DELIVERED")
        )
        total_amount = round(fake.pyfloat(min_value=5, max_value=80), 2)
        delivery_time_seconds = (
            float(fake.random_int(min=300, max=3600)) if status == "DELIVERED" else None
        )
        events.append(
            OrderEvent(
                order_id=order_id,
                restaurant_id=restaurant_id,
                courier_id=courier_id,
                zone_id=zone_id,
                event_time=_now(),
                status=status,
                total_amount=total_amount,
                delivery_time_seconds=delivery_time_seconds,
            )
        )
    return events


def generate_sample_courier_status(
    zone_count: int,
    courier_count: int,
    sample_batch_size_per_feed: int,
) -> List[CourierStatusEvent]:
    events: List[CourierStatusEvent] = []
    for _ in range(sample_batch_size_per_feed):
        courier_id = f"courier_{fake.random_int(1, courier_count)}"
        zone_id = f"zone_{fake.random_int(1, zone_count)}"
        status = fake.random_element(
            elements=("ONLINE", "OFFLINE", "ASSIGNED", "EN_ROUTE_PICKUP", "EN_ROUTE_DROPOFF", "IDLE")
        )
        active_order_id = (
            f"ord_{fake.uuid4()}" if status in ("ASSIGNED", "EN_ROUTE_PICKUP", "EN_ROUTE_DROPOFF") else None
        )
        events.append(
            CourierStatusEvent(
                courier_id=courier_id,
                zone_id=zone_id,
                event_time=_now(),
                status=status,
                active_order_id=active_order_id,
            )
        )
    return events


def generate_two_feeds_sample(
    zone_count: int,
    restaurant_count: int,
    courier_count: int,
    sample_batch_size_per_feed: int,
) -> Tuple[Iterable[Mapping], Iterable[Mapping]]:
    orders = generate_sample_orders(
        zone_count=zone_count,
        restaurant_count=restaurant_count,
        courier_count=courier_count,
        sample_batch_size_per_feed=sample_batch_size_per_feed,
    )
    couriers = generate_sample_courier_status(
        zone_count=zone_count,
        courier_count=courier_count,
        sample_batch_size_per_feed=sample_batch_size_per_feed,
    )
    return (e.to_dict() for e in orders), (e.to_dict() for e in couriers)


