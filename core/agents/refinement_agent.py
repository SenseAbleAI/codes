class RefinementAgent:
    def run(self, fingerprint, feedback):
        fingerprint.update(feedback)
        return fingerprint