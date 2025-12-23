from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from core.memory.storage import FileStorage
from core.memory.saf import SensoryAccessibilityFingerprint

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AgenticMemory:
    """Lightweight agentic memory backed by `FileStorage`.

    Responsibilities:
      - Create and manage user SAFs
      - Persist and load fingerprints
      - Record interaction logs and feedback
      - Provide simple summaries for debugging and analysis
    """

    def __init__(self, storage: Optional[FileStorage] = None):
        self.storage = storage if storage else FileStorage()

    def create_user(self, user_id: Optional[str] = None, initial: Optional[Dict[str, Any]] = None) -> str:
        """Create a new user id and initialize SAF.

        Returns the new `user_id`.
        """
        uid = user_id or str(uuid.uuid4())
        saf = SensoryAccessibilityFingerprint.from_dict(initial or {})
        self.storage.save(uid, saf.to_dict())
        # initialize empty interactions log
        self.storage.save(f"{uid}__interactions", [])
        logger.debug("Created user %s", uid)
        return uid

    def list_users(self) -> List[str]:
        """Return a list of user ids known to the file storage.

        Note: `FileStorage` lists files in the store; this implementation
        filters out interaction-log keys.
        """
        try:
            # FileStorage does not expose a listing API; fallback to exposing
            # underlying path if available.
            base = getattr(self.storage, "base_path", None)
            if not base:
                return []
            import os

            ids = []
            for f in os.listdir(base):
                if not f.endswith(".json"):
                    continue
                key = f[:-5]
                if key.endswith("__interactions"):
                    continue
                ids.append(key)
            return ids
        except Exception:
            return []

    def load_fingerprint(self, user_id: str) -> SensoryAccessibilityFingerprint:
        data = self.storage.load(user_id)
        if data is None:
            return SensoryAccessibilityFingerprint()
        return SensoryAccessibilityFingerprint.from_dict(data)

    def save_fingerprint(self, user_id: str, fingerprint: SensoryAccessibilityFingerprint) -> None:
        self.storage.save(user_id, fingerprint.to_dict())

    def log_interaction(self, user_id: str, event: Dict[str, Any]) -> None:
        """Append an interaction event to the user's interaction log."""
        key = f"{user_id}__interactions"
        logs = self.storage.load(key) or []
        logs.append(event)
        # keep log bounded
        if len(logs) > 2000:
            logs = logs[-2000:]
        self.storage.save(key, logs)

    def load_interactions(self, user_id: str) -> List[Dict[str, Any]]:
        return self.storage.load(f"{user_id}__interactions") or []

    def update_from_feedback(self, user_id: str, feedback: Dict[str, Any], learning_rate: float = 0.05) -> SensoryAccessibilityFingerprint:
        """Apply feedback to a user's SAF and persist changes.

        Feedback should conform to `SensoryAccessibilityFingerprint.update_from_feedback`.
        """
        fingerprint = self.load_fingerprint(user_id)
        fingerprint.update_from_feedback(feedback, learning_rate=learning_rate)
        self.save_fingerprint(user_id, fingerprint)
        # record feedback event
        self.log_interaction(user_id, {"type": "feedback", "payload": feedback})
        return fingerprint

    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        saf = self.load_fingerprint(user_id)
        interactions = self.load_interactions(user_id)
        return {"user_id": user_id, "saf": saf.to_dict(), "recent_interactions": interactions[-20:]}

    def delete_user(self, user_id: str) -> None:
        try:
            import os

            base = getattr(self.storage, "base_path", None)
            if not base:
                return
            p1 = os.path.join(base, f"{user_id}.json")
            p2 = os.path.join(base, f"{user_id}__interactions.json")
            for p in (p1, p2):
                if os.path.exists(p):
                    os.remove(p)
        except Exception:
            logger.exception("Failed to delete user %s", user_id)
