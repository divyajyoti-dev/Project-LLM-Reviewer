"""Score topic rows (human vs AI) using an LLM.

Scoring rubric (per user spec):
  0 — no overlap: the other side did not touch this topic at all
  1 — topic found, but the description / explanation differs
  2 — exact match: both sides say essentially the same thing

One-sided rows (where human_consensus or ai_view is null) are scored 0
without an LLM call.  All non-null pairs for a paper are batched into a
single LLM call to keep API costs low.
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
    return model.split("/", 1)[-1] if "/" in model else model


_SYSTEM = """\
You are an academic peer-review quality analyst.

You will receive a list of topics for one paper. Each topic has:
  - human_all: ALL points raised by ANY human reviewer on this topic (may be null)
  - ai_view: what the AI reviewer said about this topic (may be null)

The goal is to assess whether the AI review COVERS the human-raised points.
Score each topic with an integer 0, 1, or 2:
  0 = no coverage — AI did not touch this topic at all (ai_view is null or
      completely unrelated to what humans raised)
  1 = partial coverage — AI mentioned the topic but missed some points or nuances
      that the human reviewers raised
  2 = full coverage — AI covered all the key points the human reviewers raised
      about this topic

Also provide a one-sentence reasoning for each score.

Return a JSON object with a single key "results" whose value is an array.
Array must have the same length and order as the input.

Output format:
{"results": [
  {"topic": "robustness", "suggested_score": 1, "reasoning": "..."},
  ...
]}
"""


def score_topic_rows(
    topic_rows: list[dict[str, Any]],
    model: str,
) -> list[dict[str, Any]]:
    """Add suggested_score and reasoning to each row.  Returns enriched rows."""
    # Rows where one side is null get score=0 without an LLM call.
    needs_scoring: list[int] = []
    results: list[dict[str, Any]] = []

    for i, row in enumerate(topic_rows):
        enriched = dict(row)
        if not row.get("human_all") or not row.get("ai_view"):
            enriched["suggested_score"] = 0
            enriched["reasoning"] = "Not covered by one side."
        else:
            enriched["suggested_score"] = None
            enriched["reasoning"] = None
            needs_scoring.append(i)
        results.append(enriched)

    if not needs_scoring:
        return results

    # Batch LLM call for all non-null pairs.
    batch = [
        {
            "topic": results[i]["topic"],
            "human_all": results[i]["human_all"],
            "ai_view": results[i]["ai_view"],
        }
        for i in needs_scoring
    ]

    response = _openai_client().chat.completions.create(
        model=_model_name(model),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)
    if isinstance(parsed, dict):
        parsed = parsed.get("results") or next(iter(parsed.values()))
    if not isinstance(parsed, list):
        parsed = []

    for list_pos, row_idx in enumerate(needs_scoring):
        scored = parsed[list_pos] if list_pos < len(parsed) else {}
        results[row_idx]["suggested_score"] = int(scored.get("suggested_score", 0))
        results[row_idx]["reasoning"] = scored.get("reasoning", "")

    return results
