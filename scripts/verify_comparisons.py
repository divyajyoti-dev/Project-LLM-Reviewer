"""Second-agent verification pass for normalized topic rows.

Spawns a separate LLM call that re-examines each scored topic row and flags:
- Score looks wrong given content
- human_all or ai_view seems truncated / empty
- Topic label seems too vague or mismatched to content

Run standalone:  uv run python scripts/verify_comparisons.py
Auto-run via hook after compare_reviews.py.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai import OpenAI
from reviewer.config import load_config

_SYSTEM = """\
You are a strict peer-review auditor. You receive topic rows from a
human-vs-AI review comparison. Each row has:
  topic, human_all (all human reviewer points, or null if not covered),
  ai_view (AI reviewer view, or null if not covered).

null values are CORRECT — they mean that side did not cover the topic.
Do NOT flag null values.

Flag ONLY rows where:
  A) human_all is a non-null string with fewer than 15 words — likely truncated or placeholder
  B) ai_view is a non-null string with fewer than 15 words — likely truncated or placeholder
  C) Topic name is too vague to be meaningful (e.g. "other", "misc", "general", "various")
  D) human_all content clearly does not match the topic label (obvious mismatch)

Return JSON: {"flags": [{"paper_id": "...", "topic": "...", "issue": "...", "suggested_fix": "..."}]}
Return empty flags array if everything looks correct.
"""


def verify(cfg) -> None:
    client = OpenAI()
    model = cfg.model.split("/", 1)[-1] if "/" in cfg.model else cfg.model

    all_rows: list[dict] = []
    for slug_dir in sorted(Path("reviews").iterdir()):
        cache = slug_dir / "normalized_topics.json"
        if not cache.exists():
            continue
        rows = json.loads(cache.read_text())
        for r in rows:
            all_rows.append({
                "paper_id": slug_dir.name,
                "topic": r["topic"],
                "human_all": r.get("human_all"),
                "ai_view": r.get("ai_view"),
            })

    if not all_rows:
        print("No cached topic rows found — run compare_reviews.py first.")
        return

    print(f"Verifying {len(all_rows)} topic rows across {len(set(r['paper_id'] for r in all_rows))} papers…")

    # Batch: send all rows in one call (they're compact)
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": json.dumps(all_rows, ensure_ascii=False)},
        ],
        temperature=0.0,
    )

    raw = json.loads(response.choices[0].message.content or "{}")
    flags = raw.get("flags", [])

    if not flags:
        print("VERIFY PASS: no issues found.")
        return

    print(f"\nFLAGS ({len(flags)}):")
    for f in flags:
        print(
            f"  [{f['paper_id']}] {f['topic']}"
            f" | fix: {f.get('suggested_fix', '?')}"
            f" | {f['issue']}"
        )
    sys.exit(1)  # non-zero so hook surfaces it


if __name__ == "__main__":
    cfg = load_config()
    verify(cfg)
