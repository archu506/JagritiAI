import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_optional_user
from app.schemas.health import QueryRequest, QueryResponse, SourceOut
from app.models.health import HealthQuery
from app.services.safety import MedicalSafetyEngine
from app.services.rag import get_retriever
from app.services.ai.factory import get_ai_service
from app.services.ai.base import RetrievedSource, AIAnswer
from app.services.intent import classify, Intent
from app.services.cache import get_cached, set_cached
from app.services.myth_fact import find_myth_fact, format_myth_fact_answer

router = APIRouter(prefix="/query", tags=["query"])
safety_engine = MedicalSafetyEngine()


@router.post("", response_model=QueryResponse)
def ask_question(payload: QueryRequest, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    """
    Core demo flow, step 1-3:
    Citizen asks question -> Safety gate (red-flag detector, independent of
    the LLM) -> intent/topic classification -> RAG retrieval (topic-filtered,
    never substitutes an unrelated disease) -> cached or freshly generated
    answer with sources.
    Works for both logged-in and anonymous citizens.
    """
    safety_result = safety_engine.check(payload.question, payload.language)
    classification = classify(payload.question)

    if safety_result.block_ai_generation:
        record = HealthQuery(
            user_id=user.id if user else None,
            session_id=payload.session_id,
            question_text=payload.question,
            language=payload.language,
            ai_response_text=safety_result.override_message,
            sources=json.dumps([]),
            safety_flag=safety_result.flag.value,
            ai_provider="safety_override",
            detected_symptom_tags=json.dumps([]),
            intent="emergency",
            topic_category=classification.category.value,
            topic_tag=classification.topic_tag,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return QueryResponse(
            query_id=record.id,
            answer=safety_result.override_message,
            sources=[],
            provider="safety_override",
            safety_flag=safety_result.flag.value,
            detected_symptom_tags=[],
        )

    cached = get_cached(payload.question, payload.language)
    if cached:
        answer = AIAnswer(**cached)
    elif classification.intent == Intent.myth_fact:
        # Myth-busting is never LLM-generated - ground strictly against the
        # curated MythFact table so no fact can be invented at answer time.
        mf = find_myth_fact(db, payload.question, classification.topic_tag, payload.language)
        if mf:
            answer = AIAnswer(
                answer_text=format_myth_fact_answer(mf, payload.language),
                sources=[RetrievedSource(title="Myth vs Fact", source_name=mf.source_name or "Verified source", snippet=mf.fact)],
                provider="myth_fact_grounded",
                detected_symptom_tags=[],
            )
        else:
            retriever = get_retriever(db)
            context = retriever.retrieve(payload.question, top_k=4, language=payload.language)
            ai_service = get_ai_service()
            answer = ai_service.generate_answer(payload.question, context, payload.language)
        set_cached(payload.question, payload.language, answer.model_dump())
    else:
        retriever = get_retriever(db)
        context = retriever.retrieve(payload.question, top_k=4, language=payload.language)
        ai_service = get_ai_service()
        answer = ai_service.generate_answer(payload.question, context, payload.language)
        set_cached(payload.question, payload.language, answer.model_dump())

    record = HealthQuery(
        user_id=user.id if user else None,
        session_id=payload.session_id,
        question_text=payload.question,
        language=payload.language,
        ai_response_text=answer.answer_text,
        sources=json.dumps([s.model_dump() for s in answer.sources]),
        safety_flag=safety_result.flag.value,
        ai_provider=answer.provider,
        detected_symptom_tags=json.dumps(answer.detected_symptom_tags),
        intent=classification.intent.value,
        topic_category=classification.category.value,
        topic_tag=classification.topic_tag,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return QueryResponse(
        query_id=record.id,
        answer=answer.answer_text,
        sources=[SourceOut(**s.model_dump()) for s in answer.sources],
        provider=answer.provider,
        safety_flag=safety_result.flag.value,
        detected_symptom_tags=answer.detected_symptom_tags,
    )

