from core.difficulty.zero_shot_scorer import score_sensory_difficulty

class DifficultyAgent:
    def run(self, spans, fingerprint):
        return score_sensory_difficulty(spans, fingerprint)