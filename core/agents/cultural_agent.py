from core.culture.rag import retrieve_cultural_metaphors

class CulturalAgent:
    def run(self, span, culture):
        return retrieve_cultural_metaphors(span, culture)