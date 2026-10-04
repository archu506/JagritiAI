from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


class RetrievedSource(BaseModel):
    title: str
    source_name: str
    source_url: Optional[str] = None
    snippet: str


class AIAnswer(BaseModel):
    answer_text: str
    sources: List[RetrievedSource]
    provider: str  # 'gemini' | 'demo'
    detected_symptom_tags: List[str] = []


class AIService(ABC):
    """
    Abstraction over the generative AI backend used to answer citizen health
    questions. Concrete implementations: GeminiAIService (real API) and
    DemoAIService (offline, deterministic, no API key required).
    The app selects an implementation at startup based on whether
    GEMINI_API_KEY is configured — see services/ai/factory.py.
    """

    @abstractmethod
    def generate_answer(
        self,
        question: str,
        context_chunks: List[RetrievedSource],
        language: str = "en",
    ) -> AIAnswer:
        raise NotImplementedError
