from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_KNOWN_KEY_VARS = ("OPENAI_API_KEY", "TOGETHERAI_API_KEY", "OPENROUTER_API_KEY")


@dataclass(frozen=True)
class Config:
    model: str
    max_workers: int
    papers_dir: Path
    reviews_dir: Path


def load_config() -> Config:
    if not any(os.environ.get(v) for v in _KNOWN_KEY_VARS):
        raise EnvironmentError(
            f"No API key found. Set one of: {', '.join(_KNOWN_KEY_VARS)} in your .env file."
        )
    return Config(
        model=os.environ.get("MODEL", "openai/gpt-4o"),
        max_workers=int(os.environ.get("MAX_WORKERS", "4")),
        papers_dir=Path(os.environ.get("PAPERS_DIR", "papers")),
        reviews_dir=Path(os.environ.get("REVIEWS_DIR", "reviews")),
    )
