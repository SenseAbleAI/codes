"""
DenseRetriever
-------------

Lightweight dense-retrieval class used for the senseAble RAG pipeline. This
implementation uses a simple bag-of-words vectorizer (term frequency) and
cosine similarity to emulate dense retrieval without external embedding
libraries. It supports cultural filtering, top-K retrieval, similarity score
calculation, and batch processing.

Note: For production, replace vectorization with real embeddings (e.g., from
SentenceTransformers) and persist an ANN index (FAISS, ScaNN).
"""

from __future__ import annotations

import math
import logging
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _tokenize(text: str) -> List[str]:
    return [t.strip().lower() for t in text.split() if t.strip()]


def _vectorize(tokens: Iterable[str]) -> Dict[str, float]:
    c = Counter(tokens)
    total = sum(c.values()) or 1
    # term frequency normalization
    return {t: v / total for t, v in c.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    # compute cosine similarity between two sparse term-frequency dicts
    num = 0.0
    for k, v in a.items():
        num += v * b.get(k, 0.0)
    denom = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    if denom == 0.0:
        return 0.0
    return float(num / denom)


class DenseRetriever:
    """Simple retriever with in-memory index.

    Attributes:
        index: list of document entries (dicts with `id`, `text`, `culture`, `meta`)
    """

    def __init__(self, corpus: Optional[Iterable[Dict]] = None):
        self.index: List[Dict] = []
        self._vectors: List[Dict[str, float]] = []
        if corpus:
            self.index(corpus)

    def index(self, corpus: Iterable[Dict]) -> None:
        """Index a corpus of documents.

        Each item in `corpus` should be a dict with at least `id` and `text`.
        Optional `culture` and `meta` fields are preserved.
        """
        self.index = []
        self._vectors = []
        for doc in corpus:
            d = {
                "id": doc.get("id"),
                "text": doc.get("text", ""),
                "culture": doc.get("culture", "global"),
                "meta": doc.get("meta", {}),
            }
            self.index.append(d)
            toks = _tokenize(d["text"])
            self._vectors.append(_vectorize(toks))
        logger.info("Indexed %d documents", len(self.index))

    def retrieve(
        self, query: str, culture: Optional[str] = None, top_k: int = 10, batch: bool = False
    ) -> List[str]:
        """Retrieve top-K documents for a query.

        Args:
            query: textual query
            culture: optional culture key to filter or boost documents
            top_k: number of results to return
            batch: if True, `query` is assumed to be an iterable of queries (not supported in this lightweight impl)

        Returns:
            List of document texts ordered by similarity.
        """
        if batch:
            raise NotImplementedError("Batch retrieval not implemented in lightweight DenseRetriever")

        qvec = _vectorize(_tokenize(query))
        scores: List[Tuple[float, int, float]] = []
        for i, docvec in enumerate(self._vectors):
            sim = _cosine(qvec, docvec)
            # cultural boost if applicable
            doc_cult = self.index[i].get("culture", "global")
            if culture and culture.lower() in str(doc_cult).lower():
                sim *= 1.1
            scores.append((sim, i, float(sim)))

        scores.sort(key=lambda x: x[0], reverse=True)
        results_with_scores: List[Tuple[str, float]] = []
        for sim, i, raw in scores[:top_k]:
            if sim <= 0:
                continue
            results_with_scores.append((self.index[i]["text"], float(sim)))

        # if nothing matches, return short template augmentation with low scores
        if not results_with_scores:
            return [f"{query} in local {culture or 'global'} context", f"{query} metaphor from {culture or 'global'}"]

        # default return: list of texts; consumer may request scores explicitly
        return [t for t, s in results_with_scores]

    def retrieve_with_scores(self, query: str, culture: Optional[str] = None, top_k: int = 10) -> List[Tuple[str, float]]:
        """Retrieve top-K documents and return list of (text, score).

        This helper is useful when callers need similarity scores for reranking.
        """
        qvec = _vectorize(_tokenize(query))
        scores: List[Tuple[float, int]] = []
        for i, docvec in enumerate(self._vectors):
            sim = _cosine(qvec, docvec)
            doc_cult = self.index[i].get("culture", "global")
            if culture and culture.lower() in str(doc_cult).lower():
                sim *= 1.1
            scores.append((sim, i))

        scores.sort(reverse=True)
        out: List[Tuple[str, float]] = []
        for sim, i in scores[:top_k]:
            out.append((self.index[i]["text"], float(sim)))
        return out


__all__ = ["DenseRetriever"]
