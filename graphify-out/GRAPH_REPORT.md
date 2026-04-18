# Graph Report - /Users/divyajyoti/dev/Project-LLM-Reviewer  (2026-04-17)

## Corpus Check
- 5 files · ~22,314 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 19 nodes · 30 edges · 4 communities detected
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]

## God Nodes (most connected - your core abstractions)
1. `run_paper_review()` - 6 edges
2. `is_already_reviewed()` - 6 edges
3. `pdf_slug()` - 5 edges
4. `save_review()` - 5 edges
5. `build_review_record()` - 4 edges
6. `main()` - 3 edges
7. `load_config()` - 3 edges
8. `sha256_of_file()` - 3 edges
9. `review_dir()` - 3 edges
10. `Config` - 2 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `is_already_reviewed()`  [INFERRED]
  /Users/divyajyoti/dev/Project-LLM-Reviewer/scripts/run_reviews.py → /Users/divyajyoti/dev/Project-LLM-Reviewer/src/reviewer/storage.py
- `run_paper_review()` --calls--> `pdf_slug()`  [INFERRED]
  /Users/divyajyoti/dev/Project-LLM-Reviewer/src/reviewer/pipeline.py → /Users/divyajyoti/dev/Project-LLM-Reviewer/src/reviewer/storage.py
- `run_paper_review()` --calls--> `save_review()`  [INFERRED]
  /Users/divyajyoti/dev/Project-LLM-Reviewer/src/reviewer/pipeline.py → /Users/divyajyoti/dev/Project-LLM-Reviewer/src/reviewer/storage.py
- `main()` --calls--> `load_config()`  [INFERRED]
  /Users/divyajyoti/dev/Project-LLM-Reviewer/scripts/run_reviews.py → /Users/divyajyoti/dev/Project-LLM-Reviewer/src/reviewer/config.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.54
Nodes (7): build_review_record(), is_already_reviewed(), pdf_slug(), Return (should_skip, reason). should_skip=True means an up-to-date review exists, review_dir(), save_review(), sha256_of_file()

### Community 1 - "Community 1"
Cohesion: 0.5
Nodes (3): Config, load_config(), main()

### Community 2 - "Community 2"
Cohesion: 0.6
Nodes (4): _call_review_with_retry(), Review a single paper. Blocking; safe to call from a thread pool., ReviewResult, run_paper_review()

### Community 3 - "Community 3"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **2 isolated node(s):** `Review a single paper. Blocking; safe to call from a thread pool.`, `Return (should_skip, reason). should_skip=True means an up-to-date review exists`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 3`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `is_already_reviewed()` connect `Community 0` to `Community 1`?**
  _High betweenness centrality (0.474) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 1` to `Community 0`?**
  _High betweenness centrality (0.359) - this node is a cross-community bridge._
- **Why does `run_paper_review()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `run_paper_review()` (e.g. with `pdf_slug()` and `save_review()`) actually correct?**
  _`run_paper_review()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Review a single paper. Blocking; safe to call from a thread pool.`, `Return (should_skip, reason). should_skip=True means an up-to-date review exists` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._