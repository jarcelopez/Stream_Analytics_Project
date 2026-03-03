from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence

from fastavro import parse_schema, writer


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json_events(path: Path, events: Iterable[Mapping]) -> None:
    """
    Write events as line-delimited JSON.

    Each event is expected to be JSON-serializable. This helper intentionally
    keeps formatting simple and Spark-friendly.
    """
    import json

    _ensure_directory(path)
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event))
            f.write("\n")


def _load_avro_schema(schema_path: Path) -> Mapping:
    import json

    with schema_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return parse_schema(raw)


def write_avro_events(path: Path, events: Sequence[Mapping], schema_path: Path) -> None:
    """
    Write events to an AVRO file using the provided schema.

    This is intentionally minimal but validates that records conform to the
    schema and produces AVRO compatible with downstream tooling.
    """
    schema = _load_avro_schema(schema_path)
    _ensure_directory(path)
    with path.open("wb") as f:
        writer(f, schema, list(events))


