from __future__ import annotations

import argparse
from pprint import pprint

from stream_analytics.spark_jobs.parquet_inspection import (
    assert_required_columns,
    build_inspection_sql,
    read_parquet_records,
    validate_metrics_row,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect curated metrics parquet output.")
    parser.add_argument("--path", required=True, help="Parquet dataset path.")
    parser.add_argument("--limit", type=int, default=5, help="Sample row limit.")
    args = parser.parse_args()

    records = read_parquet_records(args.path, limit=args.limit)
    if not records:
        print("No rows found in parquet dataset.")
        print(build_inspection_sql(args.path))
        return 0

    assert_required_columns(records[0].keys())
    print("Schema columns in first sampled row:")
    print(sorted(records[0].keys()))
    print("")
    print("Sample rows:")
    for idx, row in enumerate(records, start=1):
        errors = validate_metrics_row(row)
        print(f"- Row {idx}: {'OK' if not errors else 'INVALID'}")
        if errors:
            for err in errors:
                print(f"  * {err}")
        pprint(row)
    print("")
    print("Spark SQL inspection query:")
    print(build_inspection_sql(args.path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
