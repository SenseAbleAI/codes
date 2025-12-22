from core.detection.sensory_detector import detect_sensory_spans
from core.difficulty.zero_shot_scorer import score_sensory_difficulty
from core.culture.rag import retrieve_cultural_metaphors
from core.stg.traversal import traverse_stg
from core.reasoning.multisensory import apply_multisensory_reasoning
from core.generation.rewrite_engine import generate_rewrites
from core.generation.constraints import validate_rewrites

def run_rewrite_pipeline(text, language, culture, fingerprint):
    sensory_spans = detect_sensory_spans(text, language)
    difficulty_scores = score_sensory_difficulty(sensory_spans, fingerprint)

    candidates = []
    for span, difficulty in zip(sensory_spans, difficulty_scores):
        metaphors = retrieve_cultural_metaphors(span, culture)
        stg_nodes = traverse_stg(span, fingerprint)
        multisensory_alternatives = apply_multisensory_reasoning(span, stg_nodes, fingerprint)
        candidates.append({
            "span": span,
            "difficulty": difficulty,
            "metaphors": metaphors,
            "alternatives": multisensory_alternatives
        })

    rewrite_candidates = generate_rewrites(text, candidates, fingerprint)
    validated = validate_rewrites(text, rewrite_candidates)

    return {
        "original": text,
        "alternatives": validated["alternatives"],
        "strategy": validated["strategy"]
    }