from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class SensoryAccessibilityFingerprint:
    """Sensory Accessibility Fingerprint (SAF).

    Holds per-modality sensitivity scores, rewrite strategy preferences,
    metaphor familiarity scores, and lightweight interaction history. This
    structure is intentionally simple and serializable; learning/update
    methods provide safe, bounded adjustments.
    """

    data: Dict[str, float] = field(default_factory=lambda: {
        "vision": 0.0,
        "hearing": 0.0,
        "smell": 0.0,
        "taste": 0.0,
        "touch": 0.0,
        # rewrite strategy priors (sum to 1.0)
        "rewrite_minimal": 0.33,
        "rewrite_gentle": 0.33,
        "rewrite_full": 0.34,
        # metaphor familiarity (0-1)
        "local_metaphor_familiarity": 0.5,
        "global_metaphor_familiarity": 0.5,
    })
    preferences: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    version: int = 1

    def validate(self) -> None:
        """Validate and normalize internal fields for safety.

        Ensures rewrite strategy probabilities sum to 1 and modality values are
        clamped to [0,1].
        """
        # clamp modalities
        for m in ("vision", "hearing", "smell", "taste", "touch"):
            self.data[m] = max(0.0, min(1.0, float(self.data.get(m, 0.0))))

        # normalize rewrite strategy probs
        rmin = float(self.data.get("rewrite_minimal", 0.0))
        rgen = float(self.data.get("rewrite_gentle", 0.0))
        rfull = float(self.data.get("rewrite_full", 0.0))
        total = max(1e-6, rmin + rgen + rfull)
        self.data["rewrite_minimal"] = rmin / total
        self.data["rewrite_gentle"] = rgen / total
        self.data["rewrite_full"] = rfull / total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": dict(self.data),
            "preferences": dict(self.preferences),
            "history": list(self.history),
            "version": int(self.version),
        }

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]] = None) -> "SensoryAccessibilityFingerprint":
        payload = payload or {}
        data = payload.get("data") or payload
        prefs = payload.get("preferences", {})
        history = payload.get("history", [])
        version = payload.get("version", 1)
        inst = cls(data=dict(data), preferences=dict(prefs), history=list(history), version=int(version))
        inst.validate()
        return inst

    def record_interaction(self, event: Dict[str, Any]) -> None:
        """Record an interaction or feedback event in the fingerprint history.

        The event should include at least `type` and optionally `timestamp`.
        """
        e = dict(event)
        if "timestamp" not in e:
            e["timestamp"] = time.time()
        self.history.append(e)
        # keep history bounded
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

    def update_from_feedback(self, feedback: Dict[str, Any], learning_rate: float = 0.05) -> None:
        """Update SAF from structured feedback.

        Feedback expected shape examples:
          {"action": "accept"|"reject"|"edit", "modality": "vision", "magnitude": 0.2}

        The method applies conservative, bounded updates and re-normalizes priors.
        """
        try:
            action = str(feedback.get("action", "")).lower()
            modality = feedback.get("modality")
            magnitude = float(feedback.get("magnitude", 1.0)) * float(learning_rate)

            if modality and modality in ("vision", "hearing", "smell", "taste", "touch"):
                # adjust modality sensitivity
                cur = float(self.data.get(modality, 0.0))
                if action == "worsen" or action == "sensitivity_inc":
                    cur = min(1.0, cur + magnitude)
                elif action == "improve" or action == "sensitivity_dec":
                    cur = max(0.0, cur - magnitude)
                self.data[modality] = cur

            # rewrite strategy feedback
            if action in ("accept", "reject", "edit"):
                if action == "accept":
                    self.data["rewrite_gentle"] = float(self.data.get("rewrite_gentle", 0.0)) + magnitude
                elif action == "reject":
                    self.data["rewrite_full"] = float(self.data.get("rewrite_full", 0.0)) + magnitude
                elif action == "edit":
                    self.data["rewrite_minimal"] = float(self.data.get("rewrite_minimal", 0.0)) + magnitude

            # update metaphor familiarity signals if provided
            if "local_metaphor_familiarity" in feedback:
                self.data["local_metaphor_familiarity"] = max(0.0, min(1.0, float(feedback["local_metaphor_familiarity"])))
            if "global_metaphor_familiarity" in feedback:
                self.data["global_metaphor_familiarity"] = max(0.0, min(1.0, float(feedback["global_metaphor_familiarity"])))

            # normalize rewrite strategy probabilities
            self.validate()

            # record feedback event
            self.record_interaction({"type": "feedback", "action": action, "modality": modality, "magnitude": magnitude})
        except Exception as exc:
            logger.exception("Failed to update SAF from feedback: %s", exc)

    def get_rewrite_strategy_probs(self) -> Dict[str, float]:
        """Return normalized rewrite strategy probabilities.

        Useful for upstream decision making.
        """
        self.validate()
        return {
            "minimal": float(self.data.get("rewrite_minimal", 0.0)),
            "gentle": float(self.data.get("rewrite_gentle", 0.0)),
            "full": float(self.data.get("rewrite_full", 0.0)),
        }

    def adjust_modality_sensitivity(self, modality: str, delta: float) -> None:
        """Apply a bounded delta to a modality sensitivity value."""
        if modality not in ("vision", "hearing", "smell", "taste", "touch"):
            raise KeyError(f"Unknown modality '{modality}'")
        self.data[modality] = max(0.0, min(1.0, float(self.data.get(modality, 0.0)) + float(delta)))

    def __repr__(self) -> str:
        return f"SAF(v={self.version}, modalities={{{', '.join(f'{k}:{v:.2f}' for k,v in self.data.items() if k in ['vision','hearing','smell','taste','touch'])}}})"