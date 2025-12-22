def select_rewrite_strategy(fingerprint):
    scores = {
        "minimal": fingerprint.data.get("rewrite_minimal", 0.33),
        "gentle": fingerprint.data.get("rewrite_gentle", 0.33),
        "full": fingerprint.data.get("rewrite_full", 0.34)
    }
    return max(scores, key=scores.get)