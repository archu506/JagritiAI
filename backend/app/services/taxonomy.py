"""
Two-level health topic taxonomy shared across RAG retrieval, intent
classification, and the Early Awareness Engine's signal aggregation.

LEVEL 1 (category) is coarse enough that generic queries ("many people have
fever") can still contribute a meaningful public-health signal even when no
specific disease is named. LEVEL 2 (topic/disease_tag) is used when the
knowledge base has a specific verified document.

Adding a new disease means adding a knowledge document with the right
topic_tag/category - not modifying this file's logic, though the taxonomy
dict itself may grow with new (topic -> category) mappings over time.
"""
from enum import Enum


class HealthCategory(str, Enum):
    fever_cluster = "fever_cluster"
    vector_borne = "vector_borne"
    water_borne = "water_borne"
    respiratory = "respiratory"
    gastrointestinal = "gastrointestinal"
    skin_allergy = "skin_allergy"
    maternal_child = "maternal_child"
    mental_health = "mental_health"
    chronic_disease = "chronic_disease"
    nutrition = "nutrition"
    vaccination = "vaccination"
    general_prevention = "general_prevention"
    emergency = "emergency"
    other = "other"


# topic_tag -> HealthCategory. This is the only place new diseases need a
# one-line registration; the knowledge document itself carries the medical
# content, this just tells the taxonomy which coarse bucket it rolls up into.
TOPIC_TO_CATEGORY = {
    "dengue": HealthCategory.vector_borne,
    "डेंगू": HealthCategory.vector_borne,
    "डेन्गु": HealthCategory.vector_borne,
    "ଡେଙ୍ଗୁ": HealthCategory.vector_borne,

    "malaria": HealthCategory.vector_borne,
    "मलेरिया": HealthCategory.vector_borne,
    "ମ୍ୟାଲେରିଆ": HealthCategory.vector_borne,

    "chikungunya": HealthCategory.vector_borne,
    "cholera": HealthCategory.water_borne,
    "typhoid": HealthCategory.water_borne,

    "diarrhea": HealthCategory.gastrointestinal,
    "diarrhoea": HealthCategory.gastrointestinal,
    "loose motion": HealthCategory.gastrointestinal,
    "दस्त": HealthCategory.gastrointestinal,
    "ओआरएस": HealthCategory.gastrointestinal,
    "झाड़ा": HealthCategory.gastrointestinal,
    "ଝାଡ଼ା": HealthCategory.gastrointestinal,
    "ଝାଡା": HealthCategory.gastrointestinal,
    "ଓଆରଏସ୍": HealthCategory.gastrointestinal,
    "ଓଆରଏସ": HealthCategory.gastrointestinal,

    "flu": HealthCategory.respiratory,
    "influenza": HealthCategory.respiratory,
    "tuberculosis": HealthCategory.respiratory,
    "rash": HealthCategory.skin_allergy,
    "diabetes": HealthCategory.chronic_disease,
    "hypertension": HealthCategory.chronic_disease,
}

# Generic symptom words that must NOT be treated as a specific disease
# mention. A query containing only these terms stays at category level
# (e.g. fever_cluster) rather than being forced onto one disease's document.
GENERIC_SYMPTOM_TERMS = {
    "fever", "cough", "pain", "ache", "tired", "fatigue", "headache",
    "nausea", "weakness", "chills", "sick", "unwell",
    "बुखार", "खांसी", "दर्द", "सिरदर्द", "थकान", "कमजोरी", "उल्टी", "चक्कर",
    "ଜ୍ୱର", "କାଶ", "ଯନ୍ତ୍ରଣା", "ମୁଣ୍ଡବିନ୍ଧା", "ଦୁର୍ବଳତା", "ବାନ୍ତି",
}


def category_for_topic(topic_tag: str) -> HealthCategory:
    return TOPIC_TO_CATEGORY.get(topic_tag.lower(), HealthCategory.other)


def known_topics() -> set:
    """Topics that exist as a registered taxonomy entry (may or may not have a KB doc yet)."""
    return set(TOPIC_TO_CATEGORY.keys())

