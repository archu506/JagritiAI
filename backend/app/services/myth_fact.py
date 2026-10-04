"""
Grounds myth_fact-intent queries against the verified MythFact table.
Deliberately does NOT call the LLM to "explain" the myth - the whole point
is that myth-busting content must come from a human-curated, sourced
knowledge entry, never be invented at generation time.
"""
import re
from sqlalchemy.orm import Session
from app.models.content import MythFact

STOPWORDS = {"the", "a", "an", "is", "are", "of", "to", "in", "for", "that", "does", "do", "it", "true"}


def _tokenize(text: str) -> set:
    words = re.findall(r"[\u0900-\u097F\u0B00-\u0B7F\w]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def find_myth_fact(db: Session, question: str, topic_tag: str | None, language: str = "en") -> MythFact | None:
    query = db.query(MythFact).filter(MythFact.language == language)
    if topic_tag:
        query = query.filter(MythFact.topic_tag == topic_tag)
    candidates = query.all()

    if not candidates:
        return None

    query_tokens = _tokenize(question)
    best, best_score = None, 0
    for mf in candidates:
        overlap = len(query_tokens & _tokenize(mf.myth))
        if overlap > best_score:
            best, best_score = mf, overlap

    return best if best_score > 0 else (candidates[0] if topic_tag else None)


def format_myth_fact_answer(mf: MythFact, language: str = "en") -> str:
    labels = {
        "en": ("MYTH", "FACT", "Source"),
        "hi": ("भ्रम", "तथ्य", "स्रोत"),
        "or": ("ଭ୍ରମ", "ତଥ୍ୟ", "ଉତ୍ସ"),
    }
    myth_l, fact_l, source_l = labels.get(language, labels["en"])
    source_line = f"\n\n{source_l}: {mf.source_name}" if mf.source_name else ""
    return f"{myth_l}: {mf.myth}\n\n{fact_l}: {mf.fact}{source_line}"
