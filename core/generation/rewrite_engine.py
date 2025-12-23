"""
rewrite_engine
---------------

Model-agnostic rewrite engine for generating accessible rewrites of input
text. Supports strategy selection (minimal/gentle/full), template-based
rewrites, quality assessment, validation preserving named entities, and a
small caching layer for repeated requests.
"""

from __future__ import annotations

import functools
import logging
import re
from typing import Dict, Iterable, List, Optional, Tuple

from core.generation.spectrum import select_rewrite_strategy
from core.generation import constraints

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# simple in-memory cache for rewrites: key -> rewritten text list
_REWRITE_CACHE: Dict[str, List[str]] = {}


def _cache_key(text: str, replacements: Iterable[Tuple[str, str]], strategy: str) -> str:
    rep_t = tuple(sorted(replacements))
    return f"{strategy}::{text}::{rep_t}"


def _preserve_named_entities(original: str, rewritten: str) -> bool:
    """Basic check to ensure capitalized tokens (proper nouns, acronyms)
    are preserved in the rewritten text. This is a heuristic; replace with a
    real NER system in production.
    """
    orig_caps = {w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_]+\b", original)}
    rew_caps = {w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_]+\b", rewritten)}
    # allow subset but prefer no loss of named tokens
    return orig_caps.issubset(rew_caps)


def _semantic_similarity(a: str, b: str) -> float:
    """Lightweight semantic similarity via Jaccard token overlap.

    Returns a score in [0,1]. Replace with embedding similarity in production.
    """
    ta = {t.strip().lower() for t in a.split() if t.strip()}
    tb = {t.strip().lower() for t in b.split() if t.strip()}
    if not ta and not tb:
        return 1.0
    inter = ta.intersection(tb)
    uni = ta.union(tb)
    return float(len(inter) / len(uni))


def validate_rewrite(original: str, rewritten: str, threshold: float = 0.4) -> bool:
    """Validate that a rewrite preserves meaning and named entities.

    Args:
        original: original text
        rewritten: candidate rewritten text
        threshold: minimal Jaccard similarity threshold

    Returns:
        True if rewrite is acceptable.
    """
    if not _preserve_named_entities(original, rewritten):
        logger.debug("Named entities not preserved between original and rewrite")
        return False
    sim = _semantic_similarity(original, rewritten)
    logger.debug("Semantic similarity: %.3f", sim)
    return sim >= threshold


def _apply_replacements(text: str, replacements: Iterable[Tuple[str, str]]) -> str:
    out = text
    for old, new in replacements:
        # simple replace; in production use token-aware substitution
        out = re.sub(re.escape(old), new, out)
    return out


def generate_rewrites(
    text: str,
    candidates: Iterable[Dict],
    fingerprint,
    strategy_override: Optional[str] = None,
    validate: bool = True,
) -> Dict:
    """Generate rewrite alternatives for `text` given detection candidates.

    Args:
        text: original text
        candidates: iterable of candidate dicts with `span` and `alternatives` fields
        fingerprint: user fingerprint used by `select_rewrite_strategy`
        strategy_override: optional strategy to force
        validate: whether to validate rewrites before returning

    Returns:
        dict with `alternatives` (ordered list) and `strategy` used
    """
    strategy = strategy_override or select_rewrite_strategy(fingerprint)
    replacements: List[Tuple[str, str]] = []
    for c in candidates:
        span = c.get("span", {})
        alts = c.get("alternatives", [])
        if not alts:
            continue
        replacements.append((span.get("token", ""), alts[0]))

    key = _cache_key(text, replacements, strategy)
    if key in _REWRITE_CACHE:
        logger.debug("Rewrite cache hit for key %s", key)
        return {"alternatives": _REWRITE_CACHE[key], "strategy": strategy}

    alternatives: List[str] = []
    if strategy == "minimal":
        alternatives = [text]

    elif strategy == "gentle":
        # produce one-per-candidate gentle replacements
        for old, new in replacements:
            alt = _apply_replacements(text, [(old, new)])
            if not validate or validate_rewrite(text, alt):
                alternatives.append(alt)
        if not alternatives:
            alternatives = [text]

    else:  # full
        rewritten = _apply_replacements(text, replacements)
        if not validate or validate_rewrite(text, rewritten):
            alternatives = [rewritten]
        else:
            # fallback to conservative option
            alternatives = [text]

    # validate alternatives via constraints module and compute quality scores
    validated = constraints.validate_rewrites(text, {"alternatives": alternatives, "strategy": strategy}, threshold=0.4)

    # compute simple quality scores for each alternative
    scored_alts: List[Tuple[str, float]] = []
    for alt in validated.get("alternatives", []):
        score = _semantic_similarity(text, alt)
        scored_alts.append((alt, float(score)))

    # sort by score descending
    scored_alts.sort(key=lambda x: x[1], reverse=True)
    final_alts = [a for a, s in scored_alts]

    # cache small results
    try:
        _REWRITE_CACHE[key] = final_alts
    except Exception:
        logger.debug("Failed to cache rewrite (non-critical)")

    return {"alternatives": final_alts, "strategy": strategy, "scores": {a: s for a, s in scored_alts}}


__all__ = ["generate_rewrites", "validate_rewrite"]
