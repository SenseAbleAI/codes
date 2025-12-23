"""
senseAble.core.detection.taxonomy
----------------------------------

Comprehensive sensory taxonomy used by the senseAble detection components.

This module defines a modality-organized taxonomy of sensory language (vision,
hearing, smell, taste, touch, cross-sensory). Each modality contains multiple
lexical categories (base keywords, verbs, adjectives, intensity markers) as
well as a cultural weight. Language variants for several target languages are
provided to help multilingual matching. The module exposes helper functions for
querying the taxonomy and computing intensity and cultural emphasis scores.

Design notes
- The taxonomy is intentionally lexically rich but not exhaustive — it is
  designed to be extended via configuration or a database in production.
- Cultural modifiers map simple culture keys (e.g., 'us', 'jp', 'mx') to
  relative emphasis weights for each modality. These are used by downstream
  scoring functions.

Copyright: This implementation is part of the senseAble research codebase.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Core taxonomy structure. Each modality contains a structured dictionary with
# lexical categories and a cultural weight that expresses a default emphasis
# (0.0-1.0) for that modality.
SENSORY_TAXONOMY: Dict[str, Dict[str, object]] = {
    "vision": {
        "base_keywords": [
            "vision", "sight", "eye", "light", "dark", "color", "colour",
            "bright", "dim", "vivid", "glare", "glow", "shadow", "shine",
        ],
        "verbs": ["see", "look", "gaze", "glimpse", "observe", "notice"],
        "adjectives": ["visible", "blinding", "dazzling", "pale", "vibrant"],
        "intensity_markers": ["faint", "mild", "strong", "intense", "blinding"],
        "cultural_weight": 0.9,
    },
    "hearing": {
        "base_keywords": [
            "sound", "noise", "tone", "audio", "voice", "silence", "ring", "buzz",
            "echo", "whisper", "shout", "scream",
        ],
        "verbs": ["hear", "listen", "sound", "ring", "buzz"],
        "adjectives": ["loud", "quiet", "deafening", "muted", "resonant"],
        "intensity_markers": ["soft", "moderate", "loud", "deafening", "piercing"],
        "cultural_weight": 0.7,
    },
    "smell": {
        "base_keywords": ["smell", "scent", "odor", "aroma", "fragrance", "reek"],
        "verbs": ["smell", "sniff", "sniffle", "inhale"],
        "adjectives": ["fragrant", "pungent", "musty", "sweet-smelling"],
        "intensity_markers": ["faint", "noticeable", "strong", "overpowering"],
        "cultural_weight": 0.6,
    },
    "taste": {
        "base_keywords": ["taste", "flavor", "flavour", "sweet", "salty", "bitter", "sour"],
        "verbs": ["taste", "savor", "sip", "chew"],
        "adjectives": ["sweet", "sour", "bitter", "savory", "spicy"],
        "intensity_markers": ["mild", "tangy", "strong", "overpowering"],
        "cultural_weight": 0.5,
    },
    "touch": {
        "base_keywords": ["touch", "feel", "texture", "soft", "rough", "smooth", "warm", "cold"],
        "verbs": ["touch", "feel", "brush", "graze"],
        "adjectives": ["soft", "rough", "coarse", "silky", "sticky"],
        "intensity_markers": ["light", "gentle", "firm", "forceful"],
        "cultural_weight": 0.8,
    },
    "cross_sensory": {
        "base_keywords": ["like", "as", "resembles", "seems", "feels", "smells like", "tastes like"],
        "verbs": [],
        "adjectives": ["metaphorical", "figurative", "analogous"],
        "intensity_markers": ["slightly", "kind of", "very", "completely"],
        "cultural_weight": 0.65,
    },
}

# Language variant adjustments. Each language maps simple suffix/prefix/diminutive
# rules or variant wordlists. These are intentionally conservative; production
# systems should use a full morphological analyzer or language models.
LANGUAGE_VARIANTS: Dict[str, Dict[str, List[str]]] = {
    "en": {"diminutives": ["-let", "-ling"], "common_suffixes": ["-ish", "-y"]},
    "es": {"diminutives": ["-ito", "-ita"], "common_suffixes": ["-oso", "-osa"]},
    "fr": {"diminutives": ["-ette"], "common_suffixes": ["-eux", "-euse"]},
    "de": {"diminutives": ["-chen", "-lein"], "common_suffixes": ["-ig", "-lich"]},
}

# Cultural modifiers map a culture key to modality emphasis adjustments. Values
# are multipliers applied to modality cultural_weight to represent relative
# prominence in a culture's communicative patterns. Keys are examples; real
# deployments should use validated cultural profiles.
CULTURAL_MODIFIERS: Dict[str, Dict[str, float]] = {
    "us": {"vision": 1.0, "hearing": 0.95, "touch": 0.9, "smell": 0.8, "taste": 0.85, "cross_sensory": 0.9},
    "jp": {"vision": 0.95, "hearing": 0.9, "touch": 0.7, "smell": 0.85, "taste": 0.9, "cross_sensory": 1.0},
    "mx": {"vision": 0.9, "hearing": 1.0, "touch": 0.95, "smell": 0.95, "taste": 1.0, "cross_sensory": 0.9},
    "global": {m: 1.0 for m in SENSORY_TAXONOMY.keys()},
}

# Intensity level mapping to difficulty score (0.0 easy - 1.0 hard). These are
# coarse buckets; downstream modules may map continuous intensity scores.
INTENSITY_LEVELS: Dict[str, float] = {
    "very_low": 0.0,
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "very_high": 1.0,
}


def _normalize_token(tok: str) -> str:
    """Simple normalizer for tokens used in keyword matching.

    Lowercases and strips punctuation for robust matching. Not a replacement
    for language-specific tokenization.
    """
    return re.sub(r"^\W+|\W+$", "", tok.strip().lower())


def get_all_sensory_keywords(language: str = "en") -> Dict[str, List[str]]:
    """Return a dictionary of modality -> flattened keyword list, including
    language variants.

    Args:
        language: ISO-like language code used to apply simple variant rules.

    Returns:
        A dict mapping modality names to lists of keyword strings.

    Raises:
        ValueError: if requested language is unknown.
    """
    if language not in LANGUAGE_VARIANTS:
        raise ValueError(f"Unsupported language '{language}' for variants")

    variants = LANGUAGE_VARIANTS[language]
    out: Dict[str, List[str]] = {}
    for modality, block in SENSORY_TAXONOMY.items():
        keywords: List[str] = []
        for cat in ("base_keywords", "verbs", "adjectives", "intensity_markers"):
            keywords.extend([_normalize_token(k) for k in block.get(cat, []) if isinstance(k, str)])

        # Add simple diminutive/suffix variants by string concatenation.
        for suf in variants.get("diminutives", []) + variants.get("common_suffixes", []):
            # keep variants small — append to a subset of adjectives only
            for adj in block.get("adjectives", [])[:3]:
                keywords.append(_normalize_token(f"{adj}{suf}"))

        out[modality] = sorted(set(keywords))

    return out


def is_sensory_keyword(token: str, language: str = "en") -> bool:
    """Return True if token appears in any sensory keyword list.

    Args:
        token: token or phrase to check
        language: language code for variant expansion

    Returns:
        Boolean indicating presence in the taxonomy.
    """
    t = _normalize_token(token)
    all_keys = get_all_sensory_keywords(language)
    return any(t in kws for kws in all_keys.values())


def get_modality_for_keyword(token: str, language: str = "en") -> Optional[str]:
    """Return the dominant modality for a given token, or None if unknown.

    If a token appears in multiple modalities this returns the modality with
    the highest base cultural_weight as a simple tie-breaker.
    """
    t = _normalize_token(token)
    all_keys = get_all_sensory_keywords(language)
    candidates: List[str] = [m for m, kws in all_keys.items() if t in kws]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    # tie-breaker: choose modality with larger cultural_weight
    best = max(candidates, key=lambda m: SENSORY_TAXONOMY.get(m, {}).get("cultural_weight", 0.0))
    return best


def get_intensity_level(token: str) -> Tuple[str, float]:
    """Map an intensity marker token to an intensity level and numeric score.

    Args:
        token: intensity-related token (e.g., 'faint', 'blinding')

    Returns:
        Tuple of (level_name, score).

    Notes:
        The function uses a small heuristic map and falls back to 'medium'.
    """
    t = _normalize_token(token)
    low = {"faint", "mild", "slightly", "light"}
    medium = {"noticeable", "moderate", "kind of", "somewhat"}
    high = {"strong", "intense", "very", "piercing", "blinding"}
    very_high = {"overpowering", "deafening", "explosive"}

    if t in low:
        return "low", INTENSITY_LEVELS["low"]
    if t in medium:
        return "medium", INTENSITY_LEVELS["medium"]
    if t in high:
        return "high", INTENSITY_LEVELS["high"]
    if t in very_high:
        return "very_high", INTENSITY_LEVELS["very_high"]

    # attempt regex-based numeric detection: e.g., '2x', '100dB'
    if re.match(r"^\d+(db|dB)$", token):
        return "very_high", INTENSITY_LEVELS["very_high"]

    return "medium", INTENSITY_LEVELS["medium"]


def get_cultural_emphasis(culture: str, modality: str) -> float:
    """Return a multiplier (0.0-2.0) representing cultural emphasis for a modality.

    Args:
        culture: culture key present in CULTURAL_MODIFIERS
        modality: sensory modality name

    Returns:
        Multiplicative emphasis factor.

    Raises:
        KeyError: if modality is unknown.
    """
    if modality not in SENSORY_TAXONOMY:
        raise KeyError(f"Unknown modality '{modality}'")

    base = SENSORY_TAXONOMY[modality].get("cultural_weight", 1.0)
    modifiers = CULTURAL_MODIFIERS.get(culture, CULTURAL_MODIFIERS["global"])
    mod = modifiers.get(modality, 1.0)
    emphasis = float(base) * float(mod)
    logger.debug("Cultural emphasis for %s in %s -> %s", modality, culture, emphasis)
    return emphasis


__all__ = [
    "SENSORY_TAXONOMY",
    "LANGUAGE_VARIANTS",
    "CULTURAL_MODIFIERS",
    "INTENSITY_LEVELS",
    "get_all_sensory_keywords",
    "is_sensory_keyword",
    "get_modality_for_keyword",
    "get_intensity_level",
    "get_cultural_emphasis",
]
