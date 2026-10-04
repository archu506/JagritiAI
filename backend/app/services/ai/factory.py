import logging
from functools import lru_cache
from app.core.config import settings
from app.services.ai.base import AIService
from app.services.ai.demo_service import DemoAIService

logger = logging.getLogger(__name__)


@lru_cache
def get_ai_service() -> AIService:
    """
    AIService
    ├── GeminiAIService   (used when GEMINI_API_KEY is set and the SDK initializes)
    └── DemoAIService     (default; requires no credentials, fully offline)
    """
    if settings.GEMINI_API_KEY:
        try:
            from app.services.ai.gemini_service import GeminiAIService

            logger.info("GEMINI_API_KEY found - using GeminiAIService")
            return GeminiAIService()
        except Exception as exc:
            logger.warning("Failed to initialize GeminiAIService (%s) - falling back to DemoAIService", exc)
            return DemoAIService()

    logger.info("No GEMINI_API_KEY configured - using DemoAIService")
    return DemoAIService()
