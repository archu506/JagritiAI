"""
Minimal FAQ-style response cache. Normalizes near-duplicate phrasings
("What are the symptoms of malaria?" / "symptoms of malaria" / "Malaria
symptoms?") to the same cache key so repeated questions don't re-trigger
retrieval + LLM generation.

In-memory only (per-process). For a real multi-worker deployment this would
move to Redis, but the interface below is deliberately the seam for that -
swap _CACHE's get/set for a Redis client without touching callers.
"""
import re
import hashlib

_CACHE: dict[str, dict] = {}
_STOPWORDS = {"what", "are", "the", "is", "of", "a", "an", "how", "can", "i", "do", "does", "in"}


def _normalize(question: str, language: str) -> str:
    words = re.findall(r"[\u0900-\u097F\u0B00-\u0B7F\w]+", question.lower())
    significant = sorted(w for w in words if w not in _STOPWORDS)
    key_material = f"{language}:{','.join(significant)}"
    return hashlib.sha256(key_material.encode()).hexdigest()


def get_cached(question: str, language: str) -> dict | None:
    return _CACHE.get(_normalize(question, language))


def set_cached(question: str, language: str, value: dict) -> None:
    _CACHE[_normalize(question, language)] = value


def clear_cache() -> None:
    """Exposed for tests - avoids cross-test cache pollution."""
    _CACHE.clear()
