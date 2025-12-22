from core.generation.constraints import validate_rewrites

class ValidatorAgent:
    def run(self, original, rewrites):
        return validate_rewrites(original, rewrites)