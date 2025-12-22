from core.generation.spectrum import select_rewrite_strategy

def generate_rewrites(text, candidates, fingerprint):
    strategy = select_rewrite_strategy(fingerprint)
    alternatives = []

    if strategy == "minimal":
        alternatives.append(text)

    elif strategy == "gentle":
        for c in candidates:
            if c["alternatives"]:
                alternatives.append(c["alternatives"][0])
        if not alternatives:
            alternatives.append(text)

    else:
        rewritten = text
        for c in candidates:
            if c["alternatives"]:
                rewritten = rewritten.replace(c["span"]["token"], c["alternatives"][0])
        alternatives.append(rewritten)

    return {
        "alternatives": alternatives,
        "strategy": strategy
    }