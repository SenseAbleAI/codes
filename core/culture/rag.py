from core.culture.retriever import DenseRetriever
from core.culture.reranker import rerank_metaphors

retriever = DenseRetriever()

def retrieve_cultural_metaphors(span, culture):
    candidates = retriever.retrieve(span["token"], culture)
    return rerank_metaphors(candidates, span.get("fingerprint", {}))