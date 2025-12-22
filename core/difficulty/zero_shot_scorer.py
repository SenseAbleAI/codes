def score_sensory_difficulty(sensory_spans, fingerprint):
    scores = []
    for span in sensory_spans:
        modality = span["modality"]
        sensitivity = fingerprint.data.get(modality, 0.0)
        difficulty = min(1.0, 0.5 + sensitivity)
        scores.append(difficulty)
    return scores