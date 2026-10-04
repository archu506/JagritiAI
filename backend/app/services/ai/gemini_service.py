import logging
from typing import List
from app.services.ai.base import AIService, AIAnswer, RetrievedSource
from app.services.ai.demo_service import detect_symptom_tags, DemoAIService
from app.core.config import settings

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "or": "Odia"}

SYSTEM_INSTRUCTION = (
    "You are JagritiAI, a public health information assistant for India. "
    "Answer ONLY using the provided verified source excerpts. "
    "Never diagnose a specific individual's condition. Never claim to confirm "
    "a disease outbreak. If the sources do not cover the question, say so and "
    "recommend consulting a healthcare provider. Keep answers concise, factual, "
    "and cite which source each claim comes from."
)


class GeminiAIService(AIService):
    """
    Real implementation backed by Google's Gemini API. Falls back to
    DemoAIService.generate_answer's composition logic if the API call fails
    at runtime (e.g. network/quota issue), so a transient outage never
    breaks the demo.
    """

    def __init__(self):
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._genai = genai
        self._model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION,
        )
        self._fallback = DemoAIService()

    def generate_answer(
        self, question: str, context_chunks: List[RetrievedSource], language: str = "en"
    ) -> AIAnswer:
        tags = detect_symptom_tags(question)
        if not context_chunks:
            return self._fallback.generate_answer(question, context_chunks, language)

        context_text = "\n\n".join(
            f"[Source: {c.source_name} - {c.title}]\n{c.snippet}" for c in context_chunks
        )
        lang_name = LANGUAGE_NAMES.get(language, "English")
        prompt = (
            f"Respond in {lang_name}.\n\n"
            f"Verified source excerpts:\n{context_text}\n\n"
            f"Citizen question: {question}"
        )

        try:
            response = self._model.generate_content(prompt)
            text = response.text.strip()
            return AIAnswer(
                answer_text=text,
                sources=context_chunks,
                provider="gemini",
                detected_symptom_tags=tags,
            )
        except Exception as exc:  # network error, quota, safety block, etc.
            logger.warning("Gemini API call failed, falling back to DemoAIService: %s", exc)
            fallback_answer = self._fallback.generate_answer(question, context_chunks, language)
            fallback_answer.provider = "demo_fallback_after_gemini_error"
            return fallback_answer
