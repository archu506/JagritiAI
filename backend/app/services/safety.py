from enum import Enum
from pydantic import BaseModel

EMERGENCY_PATTERNS = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "unconscious", "severe bleeding", "seizure", "stroke", "heart attack",
    "not breathing", "choking", "emergency",
    "छाती में दर्द", "सांस लेने में तकलीफ", "सांस नहीं आ रही", "बेहोश",
    "अत्यधिक खून", "आपातकाल", "आपातकालीन",
    "ଛାତିରେ ଯନ୍ତ୍ରଣା", "ଶ୍ୱାସକ୍ରିୟାରେ କଷ୍ଟ", "ଶ୍ଵାସକ୍ରିୟାରେ କଷ୍ଟ", "ଅଚେତ",
    "ଜରୁରୀକାଳୀନ",
]

SELF_HARM_PATTERNS = [
    "suicidal", "want to die", "kill myself", "end my life", "self harm",
    "hurt myself",
    "आत्महत्या", "खुदकुशी", "मरना चाहता", "मरना चाहती",
    "ଆତ୍ମହତ୍ୟା", "ମରିବାକୁ ଚାହୁଁଛି",
]

EMERGENCY_MESSAGE = {
    "en": "This sounds like it may be a medical emergency. Please call 108 "
          "(India's national emergency number) or go to the nearest hospital "
          "immediately. This assistant cannot provide emergency medical care.",
    "hi": "यह एक चिकित्सा आपातकाल हो सकता है। कृपया तुरंत 108 पर कॉल करें या "
          "नज़दीकी अस्पताल जाएं। यह सहायक आपातकालीन चिकित्सा देखभाल प्रदान नहीं कर सकता।",
    "or": "ଏହା ଏକ ଚିକିତ୍ସା ଜରୁରୀକାଳୀନ ପରିସ୍ଥିତି ହୋଇପାରେ। ଦୟାକରି ତୁରନ୍ତ 108 କୁ କଲ୍ କରନ୍ତୁ କିମ୍ବା "
          "ନିକଟସ୍ଥ ଡାକ୍ତରଖାନାକୁ ଯାଆନ୍ତୁ।",
}

SELF_HARM_MESSAGE = {
    "en": "It sounds like you might be going through something very difficult. "
          "Please reach out now to the KIRAN mental health helpline at 1800-599-0019 "
          "(toll-free, 24/7), or talk to someone you trust. You deserve support.",
    "hi": "लगता है आप किसी बहुत कठिन दौर से गुज़र रहे हैं। कृपया अभी किरण मानसिक "
          "स्वास्थ्य हेल्पलाइन 1800-599-0019 (टोल-फ्री, 24/7) पर संपर्क करें।",
    "or": "ମନେ ହେଉଛି ଆପଣ ଏକ କଠିନ ସମୟ ଦେଇ ଗତି କରୁଛନ୍ତି। ଦୟାକରି KIRAN ହେଲ୍ପଲାଇନ 1800-599-0019 "
          "କୁ ସମ୍ପର୍କ କରନ୍ତୁ।",
}


class SafetyFlag(str, Enum):
    ok = "ok"
    emergency = "emergency"
    self_harm = "self_harm"


class SafetyCheckResult(BaseModel):
    flag: SafetyFlag
    override_message: str | None = None
    block_ai_generation: bool = False


class MedicalSafetyEngine:
    """
    Pre-screens every citizen question before it reaches the AI/RAG pipeline.
    Emergency and self-harm patterns short-circuit generation entirely and
    return a fixed, reviewed safe-response instead of a model-generated one -
    this is a hard safety gate, not a suggestion to the model.
    """

    def check(self, question: str, language: str = "en") -> SafetyCheckResult:
        text = question.lower()

        if any(p in text for p in SELF_HARM_PATTERNS):
            return SafetyCheckResult(
                flag=SafetyFlag.self_harm,
                override_message=SELF_HARM_MESSAGE.get(language, SELF_HARM_MESSAGE["en"]),
                block_ai_generation=True,
            )

        if any(p in text for p in EMERGENCY_PATTERNS):
            return SafetyCheckResult(
                flag=SafetyFlag.emergency,
                override_message=EMERGENCY_MESSAGE.get(language, EMERGENCY_MESSAGE["en"]),
                block_ai_generation=True,
            )

        return SafetyCheckResult(flag=SafetyFlag.ok)
