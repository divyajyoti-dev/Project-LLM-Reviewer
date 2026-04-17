from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .storage import pdf_slug, save_review


@dataclass
class ReviewResult:
    pdf_path: Path
    slug: str
    output_dir: Path
    success: bool
    error: str | None = None


def run_paper_review(
    pdf_path: Path,
    reviews_root: Path,
    model: str,
    author_notes: str = "",
) -> ReviewResult:
    """Review a single paper. Blocking; safe to call from a thread pool."""
    slug = pdf_slug(pdf_path)

    try:
        review, markdown, _paper_text = _call_review_with_retry(
            pdf_path=pdf_path,
            model=model,
            author_notes=author_notes,
        )
        output_dir = save_review(
            reviews_root=reviews_root,
            pdf_path=pdf_path,
            model=model,
            review=review,
            markdown=markdown,
        )
        return ReviewResult(pdf_path=pdf_path, slug=slug, output_dir=output_dir, success=True)
    except Exception as exc:
        return ReviewResult(
            pdf_path=pdf_path,
            slug=slug,
            output_dir=reviews_root / slug,
            success=False,
            error=str(exc),
        )


@retry(
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True,
)
def _call_review_with_retry(pdf_path: Path, model: str, author_notes: str):
    from coarse import review_paper  # deferred so tests can mock it
    return review_paper(
        pdf_path=pdf_path,
        model=model,
        skip_cost_gate=True,
        author_notes=author_notes,
    )
