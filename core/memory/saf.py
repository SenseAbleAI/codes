class SensoryAccessibilityFingerprint:
    def __init__(self, data=None):
        if data is None:
            self.data = {
                "vision": 0.0,
                "hearing": 0.0,
                "smell": 0.0,
                "taste": 0.0,
                "touch": 0.0,
                "rewrite_minimal": 0.33,
                "rewrite_gentle": 0.33,
                "rewrite_full": 0.34,
                "local_metaphor_familiarity": 0.5,
                "global_metaphor_familiarity": 0.5
            }
        else:
            self.data = data

    def update(self, feedback, learning_rate=0.05):
        if feedback == "accept":
            self.data["rewrite_gentle"] += learning_rate
        elif feedback == "reject":
            self.data["rewrite_full"] += learning_rate
        elif feedback == "edit":
            self.data["rewrite_minimal"] += learning_rate

        total = (
            self.data["rewrite_minimal"] +
            self.data["rewrite_gentle"] +
            self.data["rewrite_full"]
        )

        self.data["rewrite_minimal"] /= total
        self.data["rewrite_gentle"] /= total
        self.data["rewrite_full"] /= total

    def to_dict(self):
        return self.data

    @classmethod
    def from_dict(cls, data):
        return cls(data=data)