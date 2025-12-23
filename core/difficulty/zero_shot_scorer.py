"""
zero_shot_scorer
-----------------

Lightweight zero-shot difficulty scoring for sensory spans. This module
provides multiple scoring strategies and integrates modality-specific
calibrations, intensity signals, and user profile sensitivity adjustments.

The scorer is intentionally model-agnostic and returns rich per-span scoring
metadata, including confidence for downstream decision-making.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Literal, Optional

from core.detection import taxonomy

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


Strategy = Literal["simple", "contextual", "weighted", "conservative"]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def score_sensory_difficulty(
    sensory_spans: Iterable[Dict],
    fingerprint,
    strategy: Strategy = "contextual",
    normalize: bool = True,
    calibration: Optional[Dict[str, float]] = None,
) -> List[Dict]:
    """Score sensory spans for accessibility difficulty.

    Args:
        sensory_spans: iterable of span dicts from `detect_sensory_spans()`
        fingerprint: user Sensory Accessibility Fingerprint-like object. It is
            expected to provide `.data` mapping modality->sensitivity (0-1) and
            optional `.preferences` for per-user settings.
        strategy: one of supported scoring strategies
        normalize: if True, normalize final scores to [0,1]
        calibration: optional modality calibration mapping to adjust scores

    Returns:
        A list of dicts; each entry contains:
          - `modality`, `token`, `raw_score`, `score`, `confidence`, `strategy`

    Raises:
        ValueError: if unknown strategy is provided.
    """
    results: List[Dict] = []
    calibration = calibration or {}

    for span in sensory_spans:
        try:
            modality = span.get("modality")
            base_sensitivity = float(getattr(fingerprint, "data", {}).get(modality, 0.0))
            user_pref = float(getattr(fingerprint, "preferences", {}).get(modality, 0.0)) if hasattr(fingerprint, "preferences") else 0.0

            # intensity contribution
            intensity = span.get("intensity")
            intensity_score = 0.0
            if intensity and isinstance(intensity, (list, tuple)):
                intensity_score = float(intensity[1])

            # taxonomy cultural emphasis influences perceived difficulty
            culture = span.get("culture", "global")
            try:
                cultural_emph = taxonomy.get_cultural_emphasis(culture, modality)
            except Exception:
                cultural_emph = 1.0

            # base raw score depending on strategy
            if strategy == "simple":
                raw = 0.5 * base_sensitivity + 0.5 * intensity_score
            elif strategy == "contextual":
                # contextual: respects token confidence and local intensity
                conf = float(span.get("confidence", 0.5))
                raw = (0.4 * base_sensitivity) + (0.4 * intensity_score) + (0.2 * conf * cultural_emph)
            elif strategy == "weighted":
                # weighted: uses user preferences more strongly
                raw = (0.3 * base_sensitivity) + (0.5 * user_pref) + (0.2 * intensity_score * cultural_emph)
            elif strategy == "conservative":
                # conservative: bias towards higher difficulty to be safe
                raw = max(0.7 * base_sensitivity, 0.6 * intensity_score)
            else:
                raise ValueError(f"Unknown strategy '{strategy}'")

            # apply calibration per modality
            calib = float(calibration.get(modality, 1.0))
            raw *= calib

            # confidence: combination of detector confidence and calibration trust
            detector_conf = float(span.get("confidence", 0.5))
            calib_conf = 1.0 if calib == 1.0 else 0.8
            confidence = _clamp01(detector_conf * calib_conf)

            score = _clamp01(raw)
            if normalize:
                # simple normalization; could use mean/std in future
                score = _clamp01(score)

            results.append(
                {
                    "modality": modality,
                    "token": span.get("token"),
                    "raw_score": raw,
                    "score": score,
                    "confidence": confidence,
                    "strategy": strategy,
                }
            )
        except Exception as exc:  # defensive: do not break pipeline on one bad span
            logger.exception("Error scoring span %s: %s", span, exc)
            results.append({"modality": span.get("modality"), "token": span.get("token"), "raw_score": 0.0, "score": 0.0, "confidence": 0.0, "strategy": strategy})

    return results


__all__ = ["score_sensory_difficulty"]
