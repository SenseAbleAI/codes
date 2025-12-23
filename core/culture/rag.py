"""
rag
---

Retrieval-Augmented Generation (RAG) orchestration for culturally-grounded
metaphor retrieval used by senseAble.

This module coordinates query expansion, dense retrieval, cultural filtering,
re-ranking, and fallback strategies when candidate metaphors are scarce. The
implementation is intentionally modular so that real embedding services and
re-rankers can be plugged in.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Tuple

from core.culture.retriever import DenseRetriever
from core.culture.reranker import rerank_metaphors
from core.detection import taxonomy
from typing import List, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

_retriever = DenseRetriever()


def _expand_query(token: str, modality: Optional[str] = None, language: str = "en") -> List[str]:
    """Simple query expansion to improve recall for metaphor retrieval.

    The expansion produces related words and cross-modal forms. In production
    this should be replaced with embedding nearest-neighbors or controlled
    paraphrase generation.
    """
    q = token.strip()
    expansions = [q]
    # add modality keywords
    if modality and modality in taxonomy.SENSORY_TAXONOMY:
        expansions += taxonomy.SENSORY_TAXONOMY[modality].get("base_keywords", [])[:3]
    # cross-sensory expansion: put the token into simple similes
    expansions += [f"{q} like a {x}" for x in taxonomy.SENSORY_TAXONOMY.get("vision", {}).get("base_keywords", [])[:2]]
    # language variants: add diminutive suffixes where applicable
    variants = taxonomy.LANGUAGE_VARIANTS.get(language, {})
    for suf in variants.get("diminutives", [])[:2]:
        expansions.append(f"{q}{suf}")
    # de-duplicate
    seen = set()
    out = []
    for e in expansions:
        ee = e.lower()
        if ee not in seen:
            seen.add(ee)
            out.append(e)
    logger.debug("Query expansions for '%s' -> %s", token, out)
    return out


def _cultural_filter(candidates: Iterable[str], culture: str) -> List[str]:
    """Filter or reweight candidates based on cultural markers.

    This very small filter prefers candidates that contain the culture string
    or are short and idiomatic. Production systems should use cultural
    metadata on documents.
    """
    out: List[Tuple[float, str]] = []
    for c in candidates:
        score = 1.0
        if culture.lower() in c.lower():
            score += 0.2
        if len(c.split()) <= 3:
            score += 0.05
        out.append((score, c))
    out.sort(reverse=True)
    return [c for _, c in out]


def retrieve_cultural_metaphors(
    span: Dict,
    culture: str = "global",
    top_k: int = 8,
    expand: bool = True,
    fallback: bool = True,
) -> List[str]:
    """Retrieve culturally-relevant metaphors for a detected sensory span.

    Workflow:
      1. Expand the query (optional)
      2. Retrieve candidates from the dense retriever for each expansion
      3. Apply light cultural filtering and re-ranking
      4. Return top-K candidates, or fallbacks if none available

    Args:
        span: detection span dict (expects `token`, `modality`, optional `fingerprint`)
        culture: cultural profile key
        top_k: number of candidates to return
        expand: whether to perform query expansion
        fallback: whether to provide a fallback when no candidates found

    Returns:
        Ordered list of metaphor candidate strings.
    """
    token = span.get("token")
    modality = span.get("modality")
    language = span.get("language", "en")

    expansions = [token]
    if expand:
        try:
            expansions = _expand_query(token, modality=modality, language=language)
        except Exception:
            expansions = [token]

    scored_candidates: List[Tuple[float, str]] = []
    for q in expansions:
        try:
            # request scores when available
            try:
                cands = _retriever.retrieve_with_scores(q, culture, top_k=top_k)
            except Exception:
                texts = _retriever.retrieve(q, culture, top_k=top_k)
                cands = [(t, 0.5) for t in texts]

            for text, sc in cands:
                scored_candidates.append((float(sc), text))
        except Exception as exc:
            logger.exception("Retriever error for query '%s': %s", q, exc)

    if not scored_candidates and fallback:
        logger.debug("No candidates retrieved; using fallback templates for '%s'", token)
        templates = [f"{token} like a distant memory", f"{token} that fills the room"]
        scored_candidates = [(0.2, t) for t in templates]

    # sort by score and apply cultural filter heuristic
    scored_candidates.sort(reverse=True)
    filtered_texts = _cultural_filter([t for _, t in scored_candidates], culture)

    try:
        fingerprint = span.get("fingerprint", {})
        reranked = rerank_metaphors(filtered_texts[: top_k * 2], fingerprint)
    except Exception:
        reranked = filtered_texts

    # return top_k unique results
    out: List[str] = []
    seen = set()
    for m in reranked:
        if m not in seen:
            seen.add(m)
            out.append(m)
        if len(out) >= top_k:
            break

    logger.debug("RAG returned %d metaphors for token '%s'", len(out), token)
    return out


__all__ = ["retrieve_cultural_metaphors"]
