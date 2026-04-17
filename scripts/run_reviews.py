#!/usr/bin/env python3
"""Review all unreviewed papers in the papers/ directory."""
from __future__ import annotations
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reviewer.config import load_config
from reviewer.pipeline import run_paper_review
from reviewer.storage import is_already_reviewed


def main() -> int:
    config = load_config()

    cwd = Path.cwd()
    papers_dir = config.papers_dir if config.papers_dir.is_absolute() else cwd / config.papers_dir
    reviews_dir = config.reviews_dir if config.reviews_dir.is_absolute() else cwd / config.reviews_dir

    if not papers_dir.exists():
        print(f"ERROR: papers directory not found: {papers_dir}")
        print("Create it and drop PDF files in, then re-run.")
        return 1

    reviews_dir.mkdir(parents=True, exist_ok=True)

    all_pdfs = sorted(papers_dir.glob("*.pdf"))
    if not all_pdfs:
        print(f"No PDF files found in {papers_dir}")
        return 0

    to_review = []
    for pdf in all_pdfs:
        skip, reason = is_already_reviewed(reviews_dir, pdf)
        status = "SKIP " if skip else "QUEUE"
        print(f"  {status}  {pdf.name}  ({reason})")
        if not skip:
            to_review.append(pdf)

    if not to_review:
        print("\nAll papers are already reviewed.")
        return 0

    workers = min(config.max_workers, len(to_review))
    print(f"\nReviewing {len(to_review)} paper(s) with {workers} worker(s)...\n")

    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                run_paper_review,
                pdf_path=pdf,
                reviews_root=reviews_dir,
                model=config.model,
            ): pdf
            for pdf in to_review
        }
        for future in as_completed(futures):
            result = future.result()
            if result.success:
                print(f"  DONE  {result.pdf_path.name}  ->  {result.output_dir}")
            else:
                print(f"  FAIL  {result.pdf_path.name}  error: {result.error}")
            results.append(result)

    succeeded = sum(1 for r in results if r.success)
    failed = len(results) - succeeded
    print(f"\nDone: {succeeded} succeeded, {failed} failed.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
