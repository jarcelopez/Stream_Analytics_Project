from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from fastavro import parse_schema, validation


def _load_jsonl(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _project_root(project_root: Path | None) -> Path:
    return Path(project_root) if project_root is not None else Path(__file__).resolve().parents[2]


def test_order_events_edge_cases_validate_against_avro_schema(project_root: Path | None = None) -> None:
    """
    The curated order_events edge-case examples must conform to the AVRO schema.
    """
    base = _project_root(project_root)

    schema_path = base / "stream_analytics" / "generator" / "schemas" / "order_events.avsc"
    examples_path = (
        base
        / "samples"
        / "generator"
        / "order_events"
        / "json"
        / "edge_cases"
        / "order_events_edge_cases.jsonl"
    )

    assert schema_path.is_file(), f"Missing AVRO schema: {schema_path}"
    assert examples_path.is_file(), f"Missing curated examples: {examples_path}"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    parsed_schema = parse_schema(schema)

    records = _load_jsonl(examples_path)
    assert records, "Expected at least one curated order_events edge-case record"

    for rec in records:
        assert validation.validate(rec, parsed_schema), f"Record failed AVRO validation: {rec}"


def test_order_events_edge_cases_cover_key_semantics(project_root: Path | None = None) -> None:
    """
    Curated order_events edge-case examples should illustrate duplicates, missing steps,
    and impossible durations as described in the docs.
    """
    base = _project_root(project_root)
    examples_path = (
        base
        / "samples"
        / "generator"
        / "order_events"
        / "json"
        / "edge_cases"
        / "order_events_edge_cases.jsonl"
    )
    records = _load_jsonl(examples_path)
    assert records, "Expected curated order_events edge-case records"

    # Duplicates: at least one (order_id, event_time, status) combination appears more than once.
    dup_key_counts: Counter[tuple[Any, Any, Any]] = Counter(
        (rec.get("order_id"), rec.get("event_time"), rec.get("status")) for rec in records
    )
    assert any(count > 1 for count in dup_key_counts.values()), "Expected at least one duplicated order_event record"

    # Missing step: at least one order_id has CREATED and DELIVERED but no intermediate lifecycle statuses.
    statuses_by_order: dict[str, set[str]] = defaultdict(set)
    for rec in records:
        order_id = rec.get("order_id")
        status = rec.get("status")
        if isinstance(order_id, str) and isinstance(status, str):
            statuses_by_order[order_id].add(status)

    missing_step_order_found = any(
        {"CREATED", "DELIVERED"}.issubset(statuses)
        and not statuses.intersection({"ACCEPTED", "ASSIGNED", "PICKED_UP"})
        for statuses in statuses_by_order.values()
    )
    assert missing_step_order_found, "Expected at least one order with missing intermediate lifecycle steps"

    # Impossible duration: at least one delivered order has a very large delivery_time_seconds (> 4 hours).
    long_durations = [
        rec["delivery_time_seconds"]
        for rec in records
        if rec.get("status") == "DELIVERED"
        and isinstance(rec.get("delivery_time_seconds"), (int, float))
        and rec["delivery_time_seconds"] > 4 * 60 * 60
    ]
    assert long_durations, "Expected at least one impossible-duration example with very large delivery_time_seconds"


def test_courier_status_edge_cases_validate_against_avro_schema(project_root: Path | None = None) -> None:
    """
    The curated courier_status edge-case examples must conform to the AVRO schema.
    """
    base = _project_root(project_root)

    schema_path = base / "stream_analytics" / "generator" / "schemas" / "courier_status.avsc"
    examples_path = (
        base
        / "samples"
        / "generator"
        / "courier_status"
        / "json"
        / "edge_cases"
        / "courier_status_edge_cases.jsonl"
    )

    assert schema_path.is_file(), f"Missing AVRO schema: {schema_path}"
    assert examples_path.is_file(), f"Missing curated examples: {examples_path}"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    parsed_schema = parse_schema(schema)

    records = _load_jsonl(examples_path)
    assert records, "Expected at least one curated courier_status edge-case record"

    for rec in records:
        assert validation.validate(rec, parsed_schema), f"Record failed AVRO validation: {rec}"


def test_courier_status_edge_cases_cover_key_semantics(project_root: Path | None = None) -> None:
    """
    Curated courier_status edge-case examples should illustrate OFFLINE toggles and
    at least one mismatch where a courier is not clearly idle despite an active_order_id.
    """
    base = _project_root(project_root)
    examples_path = (
        base
        / "samples"
        / "generator"
        / "courier_status"
        / "json"
        / "edge_cases"
        / "courier_status_edge_cases.jsonl"
    )
    records = _load_jsonl(examples_path)
    assert records, "Expected curated courier_status edge-case records"

    # OFFLINE toggles: at least one courier_id appears in both ONLINE and OFFLINE states.
    statuses_by_courier: dict[str, set[str]] = defaultdict(set)
    for rec in records:
        courier_id = rec.get("courier_id")
        status = rec.get("status")
        if isinstance(courier_id, str) and isinstance(status, str):
            statuses_by_courier[courier_id].add(status)

    offline_toggle_found = any(
        {"ONLINE", "OFFLINE"}.issubset(statuses) for statuses in statuses_by_courier.values()
    )
    assert offline_toggle_found, "Expected at least one courier with ONLINE/OFFLINE toggle sequence"

    # Mismatch: at least one record where active_order_id is non-null but status is not clearly offline/idle-free.
    mismatch_found = any(
        rec.get("active_order_id") is not None and isinstance(rec.get("status"), str)
        for rec in records
    )
    assert mismatch_found, "Expected at least one courier_status record with non-null active_order_id indicating a mismatch scenario"

