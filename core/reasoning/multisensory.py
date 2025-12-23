"""
multisensory reasoning
----------------------

High-level multisensory reasoning utilities for translating sensory
expressions across modalities and generating accessible alternatives. The
module focuses on explainability: each generated alternative includes a
justification and attributes used to produce it.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List

from core.detection import taxonomy
from core.stg.graph import SensoryTranslationGraph

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def reason_about_span(
    span: Dict,
    graph: SensoryTranslationGraph,
    user_profile: Dict,
    candidates: Iterable[str] = (),
) -> List[Dict]:
    """Generate accessible alternatives and justifications for a detected span.

    Args:
        span: detection span dict (expects `token`, `modality`, `intensity`, `culture`)
        graph: STG used to propose cross-modal translations
        user_profile: user accessibility preferences
        candidates: optional list of pre-retrieved metaphor candidates

    Returns:
        A list of alternative dicts with keys: `text`, `modality`, `score`, `justification`.
    """
    token = span.get("token")
    modality = span.get("modality")
    culture = span.get("culture", "global")
    intensity = span.get("intensity")

    alternatives: List[Dict] = []

    # 1) Replicate original meaning with explicit qualifier
    qual = ""
    if intensity and isinstance(intensity, (list, tuple)):
        qual = f" ({intensity[0]})"
    alternatives.append({
        "text": f"{token}{qual}",
        "modality": modality,
        "score": 0.8,
        "justification": "Preserve original modality and intensity for meaning fidelity",
    })

    # 2) Cross-modal paraphrases sourced from STG neighbors
    try:
        start_nodes = [n.id for n in graph.nodes() if token.lower() in (n.text or "").lower()]
        for sn in start_nodes:
            for edge in graph.neighbors(sn):
                tgt = graph.get_node(edge.target)
                # create a simple paraphrase using the target node text if present
                alt_text = tgt.text or f"{tgt.modality} sensation"
                score = 0.6 / (1.0 + edge.base_cost)
                alternatives.append({
                    "text": alt_text,
                    "modality": tgt.modality,
                    "score": float(score),
                    "justification": f"Cross-modal translation via STG edge ({edge.transition_reason})",
                })
    except Exception:
        logger.exception("Error generating cross-modal paraphrases")

    # 3) Candidate metaphors (e.g., from RAG) converted into plain-language
    for c in candidates:
        alternatives.append({
            "text": c,
            "modality": "cross_sensory",
            "score": 0.55,
            "justification": "Retrieved culturally-grounded metaphor converted to paraphrase",
        })

    # 4) Safety/accessibility-focused rewrite: explicit descriptive variant
    # e.g., "bright" -> "bright light that may be discomforting"
    descriptor = ""
    if modality == "vision":
        descriptor = "a bright visual stimulus"
    elif modality == "hearing":
        descriptor = "a loud auditory stimulus"
    elif modality == "touch":
        descriptor = "a tactile sensation"
    else:
        descriptor = f"a {modality} sensation"

    alternatives.append({
        "text": f"{token} — {descriptor}",
        "modality": modality,
        "score": 0.7,
        "justification": "Accessibility-friendly explicit description",
    })

    # normalize and deduplicate preserving highest score
    seen: Dict[str, Dict] = {}
    for a in alternatives:
        t = a.get("text")
        if t in seen:
            if a.get("score", 0.0) > seen[t].get("score", 0.0):
                seen[t] = a
        else:
            seen[t] = a

    out = sorted(seen.values(), key=lambda x: -x.get("score", 0.0))
    logger.debug("Generated %d alternatives for token '%s'", len(out), token)
    return out


def apply_multisensory_reasoning(span: Dict, stg_nodes: Iterable[str], fingerprint: Optional[Dict] = None) -> List[Dict]:
    """Wrapper to produce alternatives from span and STG node ids.

    This function keeps compatibility with existing pipeline callers that
    expect `apply_multisensory_reasoning`.
    """
    # if stg_nodes contains node ids, map them to simple textual alternatives
    candidates: List[str] = []
    for n in stg_nodes:
        if isinstance(n, str):
            candidates.append(n.replace("_", " "))

    return reason_about_span(span=span, graph=SensoryTranslationGraph(), user_profile=fingerprint or {}, candidates=candidates)


__all__ = ["reason_about_span"]
