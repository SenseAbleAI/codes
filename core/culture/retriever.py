class DenseRetriever:
    def retrieve(self, query, culture):
        return [
            f"{query} in local {culture} context",
            f"{query} metaphor from {culture}"
        ]