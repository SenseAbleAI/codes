from core.detection.taxonomy import SENSORY_TAXONOMY

def detect_sensory_spans(text, language):
    spans = []
    words = text.lower().split()
    for i, word in enumerate(words):
        for modality, keywords in SENSORY_TAXONOMY.items():
            if word in keywords:
                spans.append({
                    "modality": modality,
                    "token": word,
                    "position": i
                })
    return spans