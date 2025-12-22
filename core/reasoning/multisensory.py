def apply_multisensory_reasoning(span, stg_nodes, fingerprint):
    alternatives = []
    for node in stg_nodes:
        if node != span["token"]:
            alternatives.append(f"{node} sensation")
    return alternatives