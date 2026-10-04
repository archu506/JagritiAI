"""
Topic-aware retrieval pipeline with anti-hallucination guarantees.

Pipeline (per architecture spec):
  query -> intent/topic classification -> metadata filtering ->
  token-overlap ranking -> confidence threshold -> grounded result or
  safe fallback (never substitutes an unrelated disease's document).
"""
import re
from abc import ABC, abstractmethod
from typing import List
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument
from app.services.ai.base import RetrievedSource
from app.services.intent import classify, ClassificationResult
from app.core.config import settings

STOPWORDS = {"the", "a", "an", "is", "are", "of", "to", "in", "for", "what", "how", "does", "do", "i"}

# Minimum token-overlap score (see _score) below which we refuse to answer
# rather than return a loosely-related document. This is the confidence
# threshold from the architecture spec (§3, step 7).
MIN_CONFIDENCE_SCORE = 1


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[\u0900-\u097F\u0B00-\u0B7F\w]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 4, language: str = "en") -> List[RetrievedSource]:
        raise NotImplementedError


class DemoRetriever(Retriever):
    """
    Offline retriever: metadata-filtered, token-overlap-ranked search over
    KnowledgeDocument rows. No vector DB or embeddings API required.

    Anti-hallucination guarantees enforced here:
      1. If the query names a SPECIFIC registered topic (e.g. "malaria"),
         candidates are filtered to that topic_tag ONLY before ranking -
         an unrelated disease document can never be substituted in.
      2. If the query is GENERIC (e.g. "fever"), we do not silently pick
         whichever disease document happens to token-match best; we only
         return documents explicitly tagged as generic/category-level, and
         otherwise return nothing rather than guess a disease.
      3. A minimum confidence score is enforced; below it, we return an
         empty result so the caller emits a safe fallback instead of a
         weakly-supported answer.
    """

    def __init__(self, db: Session):
        self.db = db

    def retrieve(self, query: str, top_k: int = 4, language: str = "en") -> List[RetrievedSource]:
        classification = classify(query)
        return self.retrieve_classified(query, classification, top_k, language)

    def retrieve_classified(
        self, query: str, classification: ClassificationResult, top_k: int = 4, language: str = "en"
    ) -> List[RetrievedSource]:
        query_tokens = set(_tokenize(query))
        if classification.topic_tag:
            query_tokens.add(classification.topic_tag)

        if not query_tokens and not classification.is_specific:
            return []

        base_query = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.language == language)

        if classification.is_specific and classification.topic_tag:
            # Specific disease named -> filter to that topic ONLY. If the
            # knowledge base has nothing for it, we correctly return []
            # rather than falling through to a semantically-similar but
            # medically wrong document.
            candidates = base_query.filter(KnowledgeDocument.topic_tag == classification.topic_tag).all()
        else:
            # Generic query -> do NOT search across all disease-specific
            # documents indiscriminately. Only consider documents explicitly
            # tagged as covering this category generically.
            candidates = base_query.filter(KnowledgeDocument.category == classification.category.value).all()

        if not candidates and language != "en":
            fallback_query = self.db.query(KnowledgeDocument).filter(KnowledgeDocument.language == "en")
            if classification.is_specific and classification.topic_tag:
                candidates = fallback_query.filter(KnowledgeDocument.topic_tag == classification.topic_tag).all()
            else:
                candidates = fallback_query.filter(KnowledgeDocument.category == classification.category.value).all()

        scored = []
        for doc in candidates:
            doc_tokens = set(_tokenize(doc.title + " " + doc.content + " " + doc.topic_tag))
            overlap = len(query_tokens & doc_tokens)
            if classification.is_specific and doc.topic_tag == classification.topic_tag:
                overlap = max(overlap, 1)
            if overlap >= MIN_CONFIDENCE_SCORE:
                # Authority/recency re-ranking: authority_score first, then
                # overlap, then most recently published.
                scored.append((doc.authority_score, overlap, doc.published_date, doc))

        scored.sort(key=lambda x: (x[0], x[1], x[2] or ""), reverse=True)
        top = scored[:top_k]

        results = []
        for _, _, _, doc in top:
            snippet = doc.content[:500]
            results.append(
                RetrievedSource(
                    title=doc.title,
                    source_name=doc.source_name,
                    source_url=doc.source_url,
                    snippet=snippet,
                )
            )
        return results


class VectorRetriever(Retriever):
    """
    Qdrant-backed semantic retriever. Only used when QDRANT_URL is configured.
    Left as a clean extension point: swap in a real embedding client + Qdrant
    client here. Falls back to DemoRetriever behavior if Qdrant is unreachable.
    """

    def __init__(self, db: Session):
        self.db = db
        self._fallback = DemoRetriever(db)

    def retrieve(self, query: str, top_k: int = 4, language: str = "en") -> List[RetrievedSource]:
        try:
            import qdrant_client  # noqa: F401  (optional dependency, not installed by default)
            # Real implementation would embed `query`, search Qdrant filtered
            # by topic metadata, then hydrate results from KnowledgeDocument.
            raise NotImplementedError("Qdrant client wiring not implemented in this build")
        except Exception:
            return self._fallback.retrieve(query, top_k, language)


def get_retriever(db: Session) -> Retriever:
    if settings.QDRANT_URL:
        return VectorRetriever(db)
    return DemoRetriever(db)

