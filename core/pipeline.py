from __future__ import annotations

import logging
from typing import Any, Dict, List

from core.detection.sensory_detector import detect_sensory_spans
from core.difficulty.zero_shot_scorer import score_sensory_difficulty
from core.culture.rag import retrieve_cultural_metaphors
from core.stg.traversal import traverse_stg
from core.reasoning.multisensory import apply_multisensory_reasoning
from core.generation.rewrite_engine import generate_rewrites
from core.generation.constraints import validate_rewrites

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def run_rewrite_pipeline(text: str, language: str, culture: str, fingerprint: Any) -> Dict[str, Any]:
    """Orchestrate the full rewrite pipeline for an input text.

    Steps:
      1. Detect sensory spans
      2. Score spans by difficulty
      3. Retrieve cultural metaphors
      4. Traverse STG to propose cross-modal translations
      5. Generate multisensory alternatives
      6. Produce rewrite candidates and validate them
    """
    try:
        sensory_spans = detect_sensory_spans(text, language, culture)
        difficulty_scores = score_sensory_difficulty(sensory_spans, fingerprint)

        candidates: List[Dict[str, Any]] = []
        for span, difficulty in zip(sensory_spans, difficulty_scores):
            metaphors = retrieve_cultural_metaphors(span, culture)
            stg_nodes = traverse_stg(span, fingerprint)
            multisensory_alternatives = apply_multisensory_reasoning(span, stg_nodes, fingerprint)
            candidates.append({
                "span": span,
                "difficulty": difficulty,
                "metaphors": metaphors,
                "alternatives": multisensory_alternatives,
            })

        rewrite_candidates = generate_rewrites(text, candidates, fingerprint)
        validated = validate_rewrites(text, rewrite_candidates)

        return {"original": text, "alternatives": validated.get("alternatives", []), "strategy": validated.get("strategy")}
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        # safe fallback: return original text
        return {"original": text, "alternatives": [text], "strategy": "minimal"}