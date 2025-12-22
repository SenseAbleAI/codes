from core.generation.rewrite_engine import generate_rewrites

class RewriteAgent:
    def run(self, text, candidates, fingerprint):
        return generate_rewrites(text, candidates, fingerprint)