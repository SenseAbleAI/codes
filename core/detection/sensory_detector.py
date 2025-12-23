"""
sensory_detector
-----------------

Advanced sensory language detector used by the senseAble pipeline. This
module provides context-aware detection of sensory expressions in text using a
combination of lexical taxonomy lookups, light-weight linguistic preprocessing,
idiom/metaphor handling, and confidence scoring.

The implementation is intentionally model-agnostic so it can be used without
heavy ML dependencies; however, hooks are provided for integrating external
lemmatizers or embeddings in production.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from core.detection import taxonomy

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Small idiom and metaphor list for improved recall. In production this should
# be replaced with a language resource or retrieved examples from the RAG.
IDIOMS: Dict[str, List[Tuple[str, str]]] = {
    # (phrase, implied_modality)
    "as clear as day": [("vision", "as clear as day")],
    "a slap in the face": [("touch", "slap in the face")],
    "music to my ears": [("hearing", "music to my ears")],
    "smells fishy": [("smell", "smells fishy")],
}


def _simple_tokenize(text: str) -> List[Tuple[str, int, int]]:
    """Tokenize text into (token, start_char, end_char) slices.

    This is a lightweight tokenizer that preserves offsets for span reporting.
    """
    tokens: List[Tuple[str, int, int]] = []
    for m in re.finditer(r"\S+", text):
        tokens.append((m.group(0), m.start(), m.end()))
    return tokens


def _normalize(token: str) -> str:
    return re.sub(r"^\W+|\W+$", "", token).lower()


def _simple_lemmatize(token: str) -> str:
    """Very small lemmatizer heuristic for common English forms.

    This is not comprehensive; for production integrate spaCy or similar.
    """
    t = token.lower()
    # common plurals
    if t.endswith("ies"):
        return t[:-3] + "y"
    if t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    # simple past -> base
    if t.endswith("ed"):
        return t[:-2]
    if t.endswith("ing"):
        return t[:-3]
    return t


def detect_sensory_spans(
    text: str,
    language: str = "en",
    culture: str = "global",
    window: int = 3,
    lemmatizer: Optional[Callable[[str], str]] = None,
) -> List[Dict[str, object]]:
    """Detect sensory spans in text.

    The detector integrates taxonomy lookups, idiom matching, simple
    linguistic preprocessing, and context-aware scoring. Returned spans are
    dictionaries with rich metadata about detection.

    Args:
        text: input text to analyze
        language: language code used for variant expansion
        culture: cultural profile key used to modulate confidence
        window: number of tokens of context to consider on each side

    Returns:
        A list of span dictionaries. Each span has keys:
          - `modality`: detected modality name
          - `token`: the matched surface text
          - `start_char`, `end_char`: character offsets in `text`
          - `start_token`, `end_token`: token indices
          - `confidence`: float in [0,1]
          - `matches`: list of matching taxonomy fields
          - `intensity`: optional intensity tuple (level, score)
          - `language`: language used
          - `culture`: culture used

    Raises:
        ValueError: if `language` is unsupported by taxonomy helpers.
    """
    if language not in taxonomy.LANGUAGE_VARIANTS:
        raise ValueError(f"Unsupported language '{language}'")

    tokens = _simple_tokenize(text)
    token_norms = [_normalize(tok) for tok, _, _ in tokens]
    if lemmatizer:
        lemmata = [lemmatizer(t) for t in token_norms]
    else:
        lemmata = [_simple_lemmatize(t) for t in token_norms]

    # prepare keyword maps
    keyword_map = taxonomy.get_all_sensory_keywords(language)

    spans: List[Dict[str, object]] = []

    # Idiom matching (phrase-level) - simple substring search for known idioms
    for idiom, records in IDIOMS.items():
        if idiom in text.lower():
            for modality, phrase in records:
                start = text.lower().find(idiom)
                if start >= 0:
                    end = start + len(idiom)
                    confidence = 0.75 * taxonomy.get_cultural_emphasis(culture, modality)
                    spans.append({
                        "modality": modality,
                        "token": text[start:end],
                        "start_char": start,
                        "end_char": end,
                        "start_token": None,
                        "end_token": None,
                        "confidence": min(1.0, confidence),
                        "matches": ["idiom"],
                        "intensity": None,
                        "language": language,
                        "culture": culture,
                    })

    # Token-level matching with context-aware scoring
    for i, (tok, schar, echar) in enumerate(tokens):
        norm = token_norms[i]
        lemma = lemmata[i]

        # Skip empty tokens
        if not norm:
            continue

        matched_modalities: List[str] = []
        match_reasons: List[str] = []

        # exact match, lemma match, or substring in taxonomy
        for modality, kws in keyword_map.items():
            if norm in kws or lemma in kws:
                matched_modalities.append(modality)
                match_reasons.append("lexical")

        # context check: look at surrounding tokens for intensity markers
        context_tokens = token_norms[max(0, i - window) : i + window + 1]
        intensity = None
        conf_boost = 0.0
        for ctx in context_tokens:
            level, score = taxonomy.get_intensity_level(ctx)
            if level != "medium":
                intensity = (level, score)
                conf_boost = max(conf_boost, score * 0.15)

        # handle cross-sensory constructions like "smells like" or "tastes like"
        two_tok = " ".join(token_norms[i : i + 2]) if i + 1 < len(token_norms) else ""
        if two_tok in [t for t in taxonomy.get_all_sensory_keywords(language).get("cross_sensory", [])]:
            # prefer cross_sensory
            matched_modalities = ["cross_sensory"]
            match_reasons.append("cross_phrase")

        # Compose detections
        for modality in matched_modalities:
            base_emph = taxonomy.get_cultural_emphasis(culture, modality)
            # base confidence based on taxonomy presence and cultural emphasis
            base_conf = 0.5 * base_emph
            conf = min(1.0, base_conf + conf_boost)

            spans.append({
                "modality": modality,
                "token": tok,
                "start_char": schar,
                "end_char": echar,
                "start_token": i,
                "end_token": i,
                "confidence": conf,
                "matches": match_reasons or ["heuristic"],
                "intensity": intensity,
                "language": language,
                "culture": culture,
                "context_tokens": context_tokens,
            })

    # merge overlapping spans and prefer higher-confidence spans
    spans = _resolve_overlaps(spans)
    logger.debug("Detected %d sensory spans", len(spans))
    return spans


def _resolve_overlaps(spans: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Resolve overlapping spans by keeping highest-confidence spans.

    Args:
        spans: list of span dicts with `start_char`, `end_char`, and `confidence`.

    Returns:
        Filtered spans without overlaps.
    """
    if not spans:
        return []
    # sort by start then by -confidence
    spans_sorted = sorted(spans, key=lambda s: (s.get("start_char", 0), -float(s.get("confidence", 0.0))))
    result: List[Dict[str, object]] = []
    for sp in spans_sorted:
        s = sp.get("start_char")
        e = sp.get("end_char")
        if s is None or e is None:
            result.append(sp)
            continue
        overlap = False
        for existing in result[:]:
            es = existing.get("start_char")
            ee = existing.get("end_char")
            if es is None or ee is None:
                continue
            if not (e <= es or s >= ee):
                # overlapping region - keep the one with higher confidence
                if float(sp.get("confidence", 0.0)) > float(existing.get("confidence", 0.0)):
                    result.remove(existing)
                else:
                    overlap = True
        if not overlap:
            result.append(sp)
    return result


__all__ = ["detect_sensory_spans"]
