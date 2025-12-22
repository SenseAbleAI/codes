import hashlib
import numpy as np

def embed_text(text, dim=384):
    h = hashlib.sha256(text.encode()).digest()
    vec = np.frombuffer(h, dtype=np.uint8).astype(float)
    if len(vec) < dim:
        vec = np.pad(vec, (0, dim - len(vec)))
    return vec[:dim] / 255.0