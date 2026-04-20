"""SQLite access layer for gen_review.db.

Column name constants at the top can be adjusted after running:
    python scripts/inspect_db.py gen_review.db
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

# ── Schema constants (gen_review.db / Gen-Review dataset) ────────────────────
_PAPERS_TABLE = "SUBMISSION"
_PAPER_ID_COL = "id"
_PAPER_TITLE_COL = "title"

# Human reviews live in REVIEW; GENAI_REVIEW holds AI-generated reviews.
_REVIEWS_TABLE = "REVIEW"
_REVIEW_PAPER_ID_COL = "paper_id"

# Text fields concatenated into prose for the normalizer.
_REVIEW_TEXT_FIELDS = (
    "main_review",
    "summary",
    "strength",
    "weaknesses",
    "questions",
    "summary_of_the_review",
)
# ─────────────────────────────────────────────────────────────────────────────


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def match_paper(conn: sqlite3.Connection, title: str) -> dict[str, Any] | None:
    """Find a paper by title, case-insensitive. Returns first exact match,
    then falls back to a prefix/substring match on the first 60 chars."""
    title_lower = title.lower().strip()
    rows = conn.execute(
        f"SELECT * FROM {_PAPERS_TABLE}"
        f" WHERE lower(trim({_PAPER_TITLE_COL})) = ?",
        (title_lower,),
    ).fetchall()
    if rows:
        return dict(rows[0])

    # Substring fallback using the first 60 characters of the title.
    prefix = title_lower[:60]
    rows = conn.execute(
        f"SELECT * FROM {_PAPERS_TABLE}"
        f" WHERE lower({_PAPER_TITLE_COL}) LIKE ?",
        (f"%{prefix}%",),
    ).fetchall()
    return dict(rows[0]) if rows else None


def get_human_reviews(
    conn: sqlite3.Connection, paper_id: Any
) -> list[dict[str, Any]]:
    """Return all human review rows for *paper_id* from the REVIEW table."""
    rows = conn.execute(
        f"SELECT * FROM {_REVIEWS_TABLE}"
        f" WHERE {_REVIEW_PAPER_ID_COL} = ?",
        (paper_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def review_prose(review_row: dict[str, Any]) -> str:
    """Concatenate all text fields from a review row into a single string."""
    parts: list[str] = []
    for field in _REVIEW_TEXT_FIELDS:
        val = review_row.get(field)
        if val:
            parts.append(f"[{field.upper()}]\n{val.strip()}")
    return "\n\n".join(parts)
