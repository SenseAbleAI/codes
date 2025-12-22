def rerank_metaphors(candidates, fingerprint):
    scored = []
    for m in candidates:
        score = fingerprint.data.get("local_metaphor_familiarity", 0.5)
        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]