import re
from typing import List
from app.services.ai.base import AIService, AIAnswer, RetrievedSource

# Minimal offline symptom keyword tagger used by both Demo and Gemini paths.
SYMPTOM_KEYWORDS = {
    "fever": ["fever", "temperature", "chills", "बुखार", "तेज़ बुखार", "तापमान", "ଜ୍ୱର"],
    "cough": ["cough", "coughing", "खांसी", "ଖାସ"],
    "diarrhea": ["diarrhea", "loose motion", "loose motions", "दस्त", "ओआरएस", "झाड़ा", "ଝାଡ଼ା", "ଝାଡା"],
    "rash": ["rash", "skin spots", "red spots", "चकत्ते", "दाने", "ରାସ୍"],
    "breathlessness": ["breathless", "shortness of breath", "difficulty breathing", "सांस", "सांस फूलना", "ଶ୍ୱାସକ୍ରିୟାରେ କଷ୍ଟ"],
    "joint_pain": ["joint pain", "body ache", "body pain", "जोड़ों का दर्द", "दर्द", "शरीर दर्द", "ଗଣ୍ଠି ଯନ୍ତ୍ରଣା"],
    "vomiting": ["vomit", "vomiting", "nausea", "उल्टी", "मिशली", "ବାନ୍ତି"],
    "headache": ["headache", "head ache", "सिरदर्द", "सिर में दर्द", "ମୁଣ୍ଡବିନ୍ଧା"],
}

EMERGENCY_PATTERNS = [
    "chest pain", "can't breathe", "cannot breathe", "unconscious",
    "severe bleeding", "suicidal", "want to die", "kill myself",
]


def detect_symptom_tags(text: str) -> List[str]:
    text_l = text.lower()
    tags = []
    for tag, keywords in SYMPTOM_KEYWORDS.items():
        if any(kw in text_l for kw in keywords):
            tags.append(tag)
    return tags


def detect_emergency(text: str) -> bool:
    text_l = text.lower()
    return any(p in text_l for p in EMERGENCY_PATTERNS)


class DemoAIService(AIService):
    """
    Deterministic, offline stand-in for the Gemini-backed assistant.
    Produces a grounded-sounding answer strictly from the retrieved
    context_chunks (RAG results) with no external network calls, so the
    full application is demoable without any API credentials.
    """

    def generate_answer(
        self,
        question: str,
        context_chunks: List[RetrievedSource],
        language: str = "en",
    ) -> AIAnswer:
        tags = detect_symptom_tags(question)

        if not context_chunks:
            answer = self._no_context_answer(language)
        else:
            answer = self._compose_answer(question, context_chunks, language)

        return AIAnswer(
            answer_text=answer,
            sources=context_chunks,
            provider="demo",
            detected_symptom_tags=tags,
        )

    def _no_context_answer(self, language: str) -> str:
        messages = {
            "en": "I don't have verified information on this specific topic yet. "
                  "Please consult a qualified healthcare provider, or contact your nearest "
                  "Primary Health Centre for guidance.",
            "hi": "मेरे पास इस विषय पर अभी सत्यापित जानकारी उपलब्ध नहीं है। कृपया किसी योग्य "
                  "स्वास्थ्य सेवा प्रदाता से सलाह लें या अपने नज़दीकी प्राथमिक स्वास्थ्य केंद्र से संपर्क करें।",
            "or": "ମୋ ପାଖରେ ଏହି ବିଷୟରେ ଏବେ ପର୍ଯ୍ୟନ୍ତ ଯାଞ୍ଚିତ ସୂଚନା ନାହିଁ। ଦୟାକରି ଜଣେ ଯୋଗ୍ୟ "
                  "ସ୍ୱାସ୍ଥ୍ୟସେବା ପ୍ରଦାନକାରୀଙ୍କ ସହ ପରାମର୍ଶ କରନ୍ତୁ।",
        }
        return messages.get(language, messages["en"])

    def _compose_answer(self, question: str, chunks: List[RetrievedSource], language: str) -> str:
        top = chunks[:3]
        body = " ".join(c.snippet.strip() for c in top)
        # Trim to a reasonable answer length
        if len(body) > 900:
            body = body[:900].rsplit(".", 1)[0] + "."

        prefixes = {
            "en": "Based on verified health information: ",
            "hi": "सत्यापित स्वास्थ्य जानकारी के अनुसार: ",
            "or": "ଯାଞ୍ଚିତ ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା ଅନୁସାରେ: ",
        }
        disclaimer = {
            "en": " This is general health information, not a diagnosis. "
                  "Please consult a doctor for advice specific to your situation.",
            "hi": " यह सामान्य स्वास्थ्य जानकारी है, निदान नहीं है। कृपया अपनी स्थिति के "
                  "अनुसार सलाह के लिए डॉक्टर से परामर्श करें।",
            "or": " ଏହା ସାଧାରଣ ସ୍ୱାସ୍ଥ୍ୟ ସୂଚନା, ରୋଗ ନିର୍ଣ୍ଣୟ ନୁହେଁ। ଦୟାକରି ଡାକ୍ତରଙ୍କ ପରାମର୍ଶ ନିଅନ୍ତୁ।",
        }
        prefix = prefixes.get(language, prefixes["en"])
        suffix = disclaimer.get(language, disclaimer["en"])
        return f"{prefix}{body}{suffix}"
