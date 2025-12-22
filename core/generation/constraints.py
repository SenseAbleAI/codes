from difflib import SequenceMatcher

def semantic_similarity(x, y):
    return SequenceMatcher(None, x, y).ratio()

def validate_rewrites(original, rewrites, threshold=0.6):
    valid = []
    for r in rewrites["alternatives"]:
        if semantic_similarity(original, r) >= threshold:
            valid.append(r)

    if not valid:
        valid = [original]

    return {
        "alternatives": valid,
        "strategy": rewrites["strategy"]
    }