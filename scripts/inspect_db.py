"""One-shot helper: print schema + sample rows for gen_review.db.

Usage:
    python scripts/inspect_db.py gen_review.db
"""
from __future__ import annotations
import sqlite3
import sys


def inspect(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    for (table,) in tables:
        print(f"\n{'='*60}")
        print(f"TABLE: {table}")
        print("─" * 60)

        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        print(f"{'cid':<4} {'name':<30} {'type':<15} {'notnull':<8} {'dflt'}")
        for col in cols:
            print(f"{col[0]:<4} {col[1]:<30} {col[2]:<15} {col[3]:<8} {col[4]}")

        row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"\nTotal rows: {row_count:,}")

        sample = conn.execute(f"SELECT * FROM {table} LIMIT 2").fetchall()
        if sample:
            print("\nSample rows:")
            col_names = [col[1] for col in cols]
            for row in sample:
                for name, val in zip(col_names, row):
                    preview = str(val)[:120].replace("\n", " ") if val is not None else "NULL"
                    print(f"  {name}: {preview}")
                print()

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_db.py <path-to-db>")
        sys.exit(1)
    inspect(sys.argv[1])
