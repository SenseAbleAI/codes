from core.memory.storage import FileStorage
from core.memory.saf import SensoryAccessibilityFingerprint
import uuid

class AgenticMemory:
    def __init__(self, storage=None):
        self.storage = storage if storage else FileStorage()

    def create_user(self):
        user_id = str(uuid.uuid4())
        saf = SensoryAccessibilityFingerprint()
        self.storage.save(user_id, saf.to_dict())
        return user_id

    def load_fingerprint(self, user_id):
        data = self.storage.load(user_id)
        if data is None:
            return SensoryAccessibilityFingerprint()
        return SensoryAccessibilityFingerprint.from_dict(data)

    def save_fingerprint(self, user_id, fingerprint):
        self.storage.save(user_id, fingerprint.to_dict())

    def update_from_feedback(self, user_id, feedback):
        fingerprint = self.load_fingerprint(user_id)
        fingerprint.update(feedback)
        self.save_fingerprint(user_id, fingerprint)
        return fingerprint