from core.stg.traversal import traverse_stg

class STGAgent:
    def run(self, span, fingerprint):
        return traverse_stg(span, fingerprint)