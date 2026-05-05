"""Reusable NLP preprocessing utilities."""

import re
from typing import Iterable


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim ends."""
    return re.sub(r"\s+", " ", text).strip()


def basic_clean(text: str) -> str:
    """Basic text cleanup for downstream NLP steps."""
    text = text.lower()
    text = normalize_whitespace(text)
    return text


def preprocess_batch(texts: Iterable[str]) -> list[str]:
    """Apply basic cleaning to a batch of texts."""
    return [basic_clean(t) for t in texts]
