from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def pdf_slug(pdf_path: Path) -> str:
    stem = pdf_path.stem
    slug = stem.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "unnamed-paper"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def review_dir(reviews_root: Path, slug: str) -> Path:
    return reviews_root / slug


def is_already_reviewed(reviews_root: Path, pdf_path: Path) -> tuple[bool, str]:
    """Return (should_skip, reason). should_skip=True means an up-to-date review exists."""
    slug = pdf_slug(pdf_path)
    json_path = review_dir(reviews_root, slug) / "review.json"

    if not json_path.exists():
        return False, "no existing review"

    try:
        data = json.loads(json_path.read_text())
        stored_hash = data.get("paper", {}).get("sha256", "")
    except (json.JSONDecodeError, KeyError):
        return False, "existing review.json is malformed"

    current_hash = sha256_of_file(pdf_path)
    if stored_hash != current_hash:
        return False, "PDF content has changed since last review"

    return True, "review is current"


def build_review_record(pdf_path: Path, model: str, review: Any) -> dict[str, Any]:
    overview = review.overall_feedback
    comments = review.detailed_comments
    issues = getattr(overview, "issues", []) or []

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper": {
            "filename": pdf_path.name,
            "slug": pdf_slug(pdf_path),
            "sha256": sha256_of_file(pdf_path),
            "title": getattr(review, "title", ""),
            "domain": getattr(review, "domain", ""),
        },
        "model": model,
        "overview": {
            "summary": getattr(overview, "summary", ""),
            "assessment": getattr(overview, "assessment", ""),
            "issues": [
                {"title": getattr(i, "title", ""), "body": getattr(i, "body", "")}
                for i in issues
            ],
            "recommendation": getattr(overview, "recommendation", ""),
            "revision_targets": getattr(overview, "revision_targets", []),
        },
        "detailed_comments": [
            {
                "number": getattr(c, "number", ""),
                "title": getattr(c, "title", ""),
                "quote": getattr(c, "quote", ""),
                "feedback": getattr(c, "feedback", ""),
                "severity": getattr(c, "severity", ""),
            }
            for c in (comments or [])
        ],
    }


def save_review(
    reviews_root: Path,
    pdf_path: Path,
    model: str,
    review: Any,
    markdown: str,
) -> Path:
    slug = pdf_slug(pdf_path)
    out_dir = review_dir(reviews_root, slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    record = build_review_record(pdf_path, model, review)
    (out_dir / "review.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "review.md").write_text(markdown, encoding="utf-8")

    return out_dir
