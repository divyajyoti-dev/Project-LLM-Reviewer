# Task 2: Human vs AI Review Comparison Pipeline

## Context
Task 1 produced AI peer reviews for 10 papers (`reviews/{01-10}/review.json`).
Task 2 adds a structured comparison:
1. **Pull** human reviews for the same 10 papers from `gen_review.db` (Gen-Review dataset, ICLR 2018–2025).
2. **Normalize** both sides into a shared topic-based schema — merging N human reviewers per paper into one consolidated view.
3. **Compare** via AI agent: for each topic, score human vs AI coverage (0/1/2).
4. **Export** Excel for user manual labeling.

User drops `gen_review.db` into project root before running.

---

## Pipeline Stages

```
gen_review.db
    │
    ▼
[Stage 1] Match + Extract
    │  match_paper(title) → paper_id
    │  get_human_reviews(paper_id) → [reviewer_1, reviewer_2, reviewer_3, ...]
    ▼
[Stage 2] Normalize — AI agent (per paper)
    │  Input:  N human reviews (raw text)
    │  Output: {topic → {human_consensus: str, sources: [reviewer_ids]}}
    │
    │  Also normalize AI review.json → {topic → {ai_view: str}}
    ▼
[Stage 3] Merge topics
    │  Union of topics from both sides
    │  Rows where only one side covered a topic: other side = null
    ▼
[Stage 4] Compare — AI agent (per topic row)
    │  Input:  human_consensus, ai_view (either may be null)
    │  Output: {suggested_score: 0|1|2, reasoning: str}
    ▼
[Stage 5] Export → comparison_output.xlsx
```

---

## New Files

| File | Purpose |
|------|---------|
| `scripts/inspect_db.py` | One-shot schema dump — run after dropping DB in root |
| `src/reviewer/db.py` | `match_paper()`, `get_human_reviews()` |
| `src/reviewer/normalizer.py` | AI agent: consolidate N human reviews → topic dict; normalize AI review → topic dict |
| `src/reviewer/comparison.py` | AI agent: score each topic row (0/1/2) |
| `scripts/compare_reviews.py` | Orchestrator: DB → normalize → compare → Excel |

## Modified Files

| File | Change |
|------|--------|
| `src/reviewer/config.py` | Add `gen_review_db: Path` (env: `GEN_REVIEW_DB`, default: `gen_review.db`) |
| `pyproject.toml` | Add `openpyxl` dependency |

---

## Data Shapes

### After Stage 2 — normalized per paper

**Human (normalized):**
```json
{
  "robustness": {
    "human_consensus": "Reviewers 1 and 3 flagged insufficient ablation...",
    "sources": ["R1", "R3"]
  },
  "novelty": { ... }
}
```

**AI (normalized):**
```json
{
  "robustness": { "ai_view": "The approach lacks stress testing on OOD data..." },
  "clarity":    { "ai_view": "Section 3 notation is inconsistent..." }
}
```

### After Stage 3 — merged topic rows
```
topic        | human_consensus          | ai_view
-------------|--------------------------|----------
robustness   | "Reviewers 1+3 flagged…" | "Lacks OOD…"
clarity      | null                     | "Section 3…"
novelty      | "All reviewers praised…" | null
```

### Excel Output — `comparison_output.xlsx`

Columns:
| Paper ID | Paper Title | Topic | Human Consensus | AI View | AI Score | **User Label** | Notes |

- `AI Score`: 0/1/2 (AI suggested, grayed out)
- `User Label`: empty, dropdown validation 0/1/2
- Null cells clearly marked "— not covered —"
- Header frozen, filters enabled

---

## Key Design Decisions

- **Normalization is an LLM call** (same model, `openai/gpt-4o`): prompt asks it to cluster reviewer comments into named topics and produce a single consensus sentence per topic.
- **AI review normalization** maps the existing `overview.issues` + `detailed_comments` fields (already in review.json) into the same topic schema.
- **One row per topic per paper** — topics are discovered dynamically, not from a fixed taxonomy.
- **One-sided topics score 0** automatically (no LLM call needed for null rows).
- Intermediate normalized JSONs cached to `reviews/{slug}/normalized_topics.json` so re-runs are cheap.

---

## Verification
```bash
# Step 0: confirm schema (after dropping DB in root)
python scripts/inspect_db.py gen_review.db

# Step 1: run full pipeline
python scripts/compare_reviews.py

# Step 2: inspect output
open comparison_output.xlsx
```

Expected: ~10 papers × 6–12 topics ≈ 60–120 rows. User label column empty, ready to fill.
