"""Normalize human and AI reviews into aligned topic rows.

One LLM call per paper produces a list of dicts:
    [{"topic": str, "human_all": str | None, "ai_view": str | None}, ...]

human_all is a COMPLETE consolidation of every point ANY human reviewer raised
on that topic — not an average or consensus.

Results are cached to reviews/{slug}/normalized_topics.json.
"""
from __future__ import annotations
import json
from typing import Any

from openai import OpenAI

_client: OpenAI | None = None


def _openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _model_name(model: str) -> str:
    """Strip provider prefix (e.g. 'openai/gpt-4o' → 'gpt-4o')."""
    return model.split("/", 1)[-1] if "/" in model else model


_SYSTEM = """\
You are an expert academic peer-review analyst.
You will receive two sets of review material for the same paper:
  A) Multiple human reviewer comments (labelled R1, R2, …)
  B) An AI-generated review broken into issues and detailed comments

Your task:
1. Identify ALL distinct topics raised by EITHER set (e.g. "robustness",
   "novelty", "clarity", "reproducibility", "experimental_design", etc.)
2. For each topic, produce:
   - human_all: a COMPLETE consolidation of every distinct point, concern, or
     observation ANY human reviewer made about this topic. Include ALL of them —
     even if reviewers contradict each other. Attribute each point to its reviewer
     (e.g. "R1: ...; R2: ...; R3: ..."). Do NOT average, summarise, or drop any
     reviewer's point. Use null if no human reviewer mentioned this topic.
   - ai_view: COMPLETE consolidation of every issue AND detailed comment the AI
     raised about this topic. Include ALL of them — do not drop any. Format as
     "Issue: ...; Comment #N: ..." etc. Use null if AI did not cover it.
3. Use concise, lowercase_snake_case topic names.
4. Return a JSON object with a single key "topics" whose value is an array.

Output format:
{"topics": [
  {"topic": "robustness", "human_all": "R1: ...; R2: ...; R3: ...", "ai_view": "..."},
  {"topic": "clarity",    "human_all": null,                         "ai_view": "..."},
  ...
]}
"""


def _format_human_block(human_reviews: list[dict[str, Any]], prose_fn: Any) -> str:
    parts: list[str] = []
    for i, review in enumerate(human_reviews, 1):
        prose = prose_fn(review)
        if prose.strip():
            parts.append(f"=== HUMAN REVIEWER R{i} ===\n{prose}")
    return "\n\n".join(parts) if parts else "(no human reviews)"


def _format_ai_block(ai_review: dict[str, Any]) -> str:
    lines: list[str] = []
    for issue in ai_review.get("overview", {}).get("issues", []):
        lines.append(f"[ISSUE] {issue.get('title', '')}: {issue.get('body', '')}")
    for comment in ai_review.get("detailed_comments", []):
        lines.append(
            f"[COMMENT #{comment.get('number', '')}] {comment.get('title', '')}: "
            f"{comment.get('feedback', '')}"
        )
    return "\n".join(lines) if lines else "(no AI review content)"


def normalize_and_align(
    human_reviews: list[dict[str, Any]],
    ai_review: dict[str, Any],
    model: str,
    prose_fn: Any,
) -> list[dict[str, Any]]:
    """Call LLM to produce aligned topic rows for one paper.

    Args:
        human_reviews: raw review dicts from db.get_human_reviews()
        ai_review:     parsed review.json dict from task 1
        model:         model string from Config (e.g. "openai/gpt-4o")
        prose_fn:      db.review_prose — passed in to avoid circular import
    """
    human_block = _format_human_block(human_reviews, prose_fn)
    ai_block = _format_ai_block(ai_review)

    user_msg = (
        f"## HUMAN REVIEWS\n\n{human_block}\n\n"
        f"## AI-GENERATED REVIEW\n\n{ai_block}"
    )

    response = _openai_client().chat.completions.create(
        model=_model_name(model),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.1,
    )

    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        parsed = parsed.get("topics") or next(iter(parsed.values()))
    if not isinstance(parsed, list):
        parsed = []
    # Coerce string "null"/"None" → actual None
    for row in parsed:
        for key in ("human_all", "ai_view"):
            if row.get(key) in ("null", "None", ""):
                row[key] = None
    return parsed  # list[{topic, human_all, ai_view}]
