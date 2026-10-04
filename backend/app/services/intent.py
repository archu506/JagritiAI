"""
Rule-based intent + topic classifier. Deliberately NOT an LLM call - this
runs on every query before any RAG/generation happens, so it must be free
and instant (see rag pipeline design goal: minimize LLM usage).
"""
import re
from enum import Enum
from pydantic import BaseModel
from app.services.taxonomy import (
    HealthCategory, TOPIC_TO_CATEGORY, GENERIC_SYMPTOM_TERMS, category_for_topic,
)


class Intent(str, Enum):
    symptom_information = "symptom_information"
    prevention = "prevention"
    treatment_information = "treatment_information"
    emergency = "emergency"
    myth_fact = "myth_fact"
    government_scheme = "government_scheme"
    nearby_healthcare = "nearby_healthcare"
    vaccination = "vaccination"
    smalltalk = "smalltalk"
    unknown = "unknown"


INTENT_KEYWORDS = {
    Intent.myth_fact: ["myth", "is it true", "true that", "enough to prevent", "enough to cure", "rumor", "rumour", "क्या सच है", "झूठ"],
    Intent.prevention: ["how can i prevent", "how to prevent", "avoid", "protect", "precaution", "ways to prevent", "बचें", "बचाव", "रोकथाम", "उपाय", "कैसे बचें", "रखें", "ରକ୍ଷା", "ପ୍ରତିଷେଧକ", "ବଞ୍ଚିବେ", "କିପରି ରକ୍ଷା"],
    Intent.treatment_information: ["treat", "treatment", "cure", "medicine", "medication", "remedy", "इलाज", "उपचार", "दवा", "ଚିକିତ୍ସା", "ଓଷଧ"],
    Intent.government_scheme: ["scheme", "yojana", "ayushman", "government benefit", "subsidy", "योजना", "ଯୋଜନା"],
    Intent.nearby_healthcare: ["nearby", "hospital near", "clinic near", "phc", "health centre near", "where can i go", "अस्पताल", "पास", "ନିକଟସ୍ଥ"],
    Intent.vaccination: ["vaccine", "vaccination", "immunization", "immunisation", "टीका", "टीकाकरण", "ଟିକା"],
    Intent.symptom_information: ["symptom", "sign of", "signs of", "what is", "what are", "लक्षण", "संकेत", "क्या है", "क्या हैं", "ଲକ୍ଷଣ", "ସଙ୍କେତ", "କ’ଣ", "କଣ"],
    Intent.smalltalk: ["hello", "hi", "hey", "thanks", "thank you", "who are you", "नमस्ते", "नमस्कार"],
}

# Declarative-claim pattern: "X prevents Y" / "X cures Y" (third-person
# assertion) signals a myth/claim being made, distinct from "how can I
# prevent Y" (bare infinitive, a genuine prevention question).
MYTH_CLAIM_PATTERN = re.compile(r"\b(prevents|cures)\b")


class ClassificationResult(BaseModel):
    intent: Intent
    topic_tag: str | None  # specific disease/topic if explicitly named, else None
    category: HealthCategory  # always set - falls back to 'other'/'fever_cluster'
    is_specific: bool  # True if a specific registered topic was detected

TOPIC_ALIASES = {
    "dengue": ["dengue", "डेंगू", "डेन्गु", "ଡେଙ୍ଗୁ"],
    "malaria": ["malaria", "मलेरिया", "ମ୍ୟାଲେରିଆ"],
    "diarrhea": ["diarrhea", "diarrhoea", "loose motion", "दस्त", "ओआरएस", "झाड़ा", "ଝାଡ଼ା", "ଝାଡା", "ଓଆରଏସ୍", "ଓଆରଏସ"],
    "flu": ["flu", "influenza", "इन्फ्लूएंजा", "फ्लू"],
    "diabetes": ["diabetes", "मधुमेह", "डायबिटीज", "ମଧୁମେହ"],
    "rash": ["rash", "चकत्ते", "दाने", "କୁଣ୍ଡିଆ"],
    "chikungunya": ["chikungunya", "चिकुनगुनिया", "ଚିକୁନଗୁନିଆ"],
    "cholera": ["cholera", "हैजा", "ଝାଡାବାନ୍ତି"],
    "typhoid": ["typhoid", "टाइफाइड", "ଟାଇଫଏଡ୍"],
    "tuberculosis": ["tuberculosis", "टीबी", "ଯକ୍ଷ୍ମା"],
    "hypertension": ["hypertension", "उच्च रक्तचाप", "ଉଚ୍ଚ ରକ୍ତଚାପ"],
}


def _detect_topic(text_l: str) -> str | None:
    """Only returns a topic if it's explicitly named and registered in the taxonomy."""
    for canonical, aliases in TOPIC_ALIASES.items():
        for alias in aliases:
            if alias in text_l:
                return canonical
    for topic in TOPIC_TO_CATEGORY:
        if topic in text_l:
            return topic
    return None



def _detect_intent(text_l: str) -> Intent:
    if MYTH_CLAIM_PATTERN.search(text_l):
        return Intent.myth_fact
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in text_l for kw in keywords):
            return intent
    return Intent.unknown


def classify(question: str) -> ClassificationResult:
    text_l = question.lower()

    topic = _detect_topic(text_l)
    intent = _detect_intent(text_l)

    if topic:
        category = category_for_topic(topic)
        is_specific = True
    else:
        # No specific disease named. If generic symptom language is present,
        # bucket at fever_cluster/category level WITHOUT picking a disease -
        # this is the core anti-hallucination guarantee.
        has_generic_symptom = any(term in text_l for term in GENERIC_SYMPTOM_TERMS)
        category = HealthCategory.fever_cluster if has_generic_symptom else HealthCategory.other
        is_specific = False

    # symptom_information is the sensible default when a topic/generic
    # symptom is present but no other intent keyword matched.
    if intent == Intent.unknown and (topic or category == HealthCategory.fever_cluster):
        intent = Intent.symptom_information

    return ClassificationResult(intent=intent, topic_tag=topic, category=category, is_specific=is_specific)
