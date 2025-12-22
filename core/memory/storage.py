import json
import os

class StorageBackend:
    def load(self, key):
        raise NotImplementedError

    def save(self, key, value):
        raise NotImplementedError


class FileStorage(StorageBackend):
    def __init__(self, base_path="memory_store"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _path(self, key):
        return os.path.join(self.base_path, f"{key}.json")

    def load(self, key):
        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)

    def save(self, key, value):
        path = self._path(key)
        with open(path, "w") as f:
            json.dump(value, f)