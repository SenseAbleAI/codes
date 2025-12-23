"""Constraints and validation utilities for rewrite generation.

Provides semantic-similarity based validation, named-entity preservation
checks, and token-aware replacement helpers. The module is intentionally
pluggable so downstream code can pass a custom `similarity_fn` (e.g., using
embeddings) for higher-quality checks.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _default_semantic_similarity(a: str, b: str) -> float:
    """Fallback semantic similarity using token Jaccard / SequenceMatcher.

    Returns a score in [0,1]."""
    try:
        ta = {t.strip().lower() for t in a.split() if t.strip()}
        tb = {t.strip().lower() for t in b.split() if t.strip()}
        if ta and tb:
            inter = ta.intersection(tb)
            uni = ta.union(tb)
            jacc = len(inter) / max(1, len(uni))
        else:
            jacc = 0.0
        # combine with SequenceMatcher for short text robustness
        seq = SequenceMatcher(None, a, b).ratio()
        return float(0.6 * jacc + 0.4 * seq)
    except Exception:
        return 0.0


def preserve_named_entities(original: str, rewritten: str) -> bool:
    """Heuristic check to ensure capitalized named tokens are preserved.

    This is a conservative check: it extracts tokens that look like proper
    nouns (capitalized words) and ensures no named token is removed by the
    rewrite. For robust NER use a model like spaCy.
    """
    orig_caps = {w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_]+\b", original)}
    rew_caps = {w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_]+\b", rewritten)}
    if not orig_caps:
        return True
    # allow if all original capitals exist in the rewritten text
    return orig_caps.issubset(rew_caps)


def token_aware_replace(text: str, replacements: Iterable[tuple]) -> str:
    """Perform token-aware replacements using word boundaries.

    `replacements` should be an iterable of (old, new) strings. This function
    avoids partial matches inside other words by using regex word boundaries.
    """
    out = text
    for old, new in replacements:
        if not old:
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(old) + r"(?!\w)", flags=re.IGNORECASE)
        out = pattern.sub(new, out)
    return out


def validate_rewrites(original: str, rewrites: Dict, threshold: float = 0.6, similarity_fn: Optional[Callable[[str, str], float]] = None, preserve_entities: bool = True) -> Dict:
    """Validate rewrite candidates and return filtered alternatives.

    Args:
        original: original text
        rewrites: dict containing `alternatives` and `strategy`
        threshold: minimal similarity score to accept a rewrite
        similarity_fn: optional callable(a,b)->float; if None uses default
        preserve_entities: whether to enforce named-entity preservation

    Returns:
        dict with `alternatives` (filtered) and `strategy`
    """
    sim = similarity_fn or _default_semantic_similarity
    valid: List[str] = []

    for r in rewrites.get("alternatives", []):
        try:
            if preserve_entities and not preserve_named_entities(original, r):
                logger.debug("Entity preservation failed for rewrite: %s", r)
                continue
            score = float(sim(original, r))
            logger.debug("Rewrite similarity score %.3f for candidate", score)
            if score >= threshold:
                valid.append(r)
        except Exception:
            logger.exception("Error validating rewrite candidate")

    if not valid:
        # Always include the original as fallback to preserve safety
        valid = [original]

    return {"alternatives": valid, "strategy": rewrites.get("strategy")}


__all__ = [
    "_default_semantic_similarity",
    "preserve_named_entities",
    "token_aware_replace",
    "validate_rewrites",
]
