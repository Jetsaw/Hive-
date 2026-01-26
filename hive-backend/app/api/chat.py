from fastapi import APIRouter
from pydantic import BaseModel

from app.agents import ChatbotAgent, ReflectionAgent, RetrieverAgent, Trace
from app.memory.repo import save_message
from app.rag.indexer import build_or_load_structure_index, build_or_load_details_index
from app.rag.retriever import search_structure_layer, search_details_layer
from app.advisor.session_manager import get_session_manager
from app.advisor.programme_detection import detect_programme
from app.advisor.alias_resolver import resolve_aliases
from app.rag.query_router import route_query

router = APIRouter()

PROGRAMME_DETECTION_CONFIDENCE_THRESHOLD = 0.7
MAX_CONTEXT_CHUNKS = 6
STRUCTURE_LAYER_TOP_K = 3
DETAILS_LAYER_TOP_K = 3

GLOBAL_INDEX = None
GLOBAL_METAS = None

STRUCTURE_INDEX = None
STRUCTURE_METAS = None
DETAILS_INDEX = None
DETAILS_METAS = None

SESSION_MANAGER = None

CHATBOT_AGENT = ChatbotAgent()
RETRIEVER_AGENT = RetrieverAgent()
REFLECTION_AGENT = ReflectionAgent()


class ChatReq(BaseModel):
    user_id: str
    message: str


def initialize_new_rag_system():
    """Initialize the new dual-layer RAG system."""
    global STRUCTURE_INDEX, STRUCTURE_METAS, DETAILS_INDEX, DETAILS_METAS, SESSION_MANAGER
    
    if STRUCTURE_INDEX is None:
        STRUCTURE_INDEX, STRUCTURE_METAS = build_or_load_structure_index()
    
    if DETAILS_INDEX is None:
        DETAILS_INDEX, DETAILS_METAS = build_or_load_details_index()
    
    if SESSION_MANAGER is None:
        SESSION_MANAGER = get_session_manager()


@router.post("/chat")
async def chat(req: ChatReq):
    user_id = (req.user_id or "").strip()
    question = (req.message or "").strip()

    if not user_id or not question:
        return {"answer": "Please enter a message."}

    # Initialize new RAG system if needed
    initialize_new_rag_system()

    trace = Trace()
    save_message(user_id, "user", question)

    session = SESSION_MANAGER.get_session(user_id)
    
    detection = detect_programme(
        question, 
        SESSION_MANAGER.get_context(user_id)
    )
    
    if detection.programme and detection.confidence > PROGRAMME_DETECTION_CONFIDENCE_THRESHOLD and not session.programme:
        SESSION_MANAGER.set_programme(user_id, detection.programme)
        session = SESSION_MANAGER.get_session(user_id)
    
    route = route_query(question, session)
    
    course_codes = route.detected_course_codes.copy() if route.detected_course_codes else []
    
    if route.requires_course_code and not course_codes:
        resolved = resolve_aliases(question, session.programme)
        course_codes.extend([r['course_code'] for r in resolved])
    
    results = []
    context_parts = []
    
    if route.should_query_structure and STRUCTURE_INDEX and STRUCTURE_INDEX.ntotal > 0:
        structure_results = search_structure_layer(
            STRUCTURE_INDEX,
            STRUCTURE_METAS,
            question,
            programme=session.programme,
            top_k=STRUCTURE_LAYER_TOP_K
        )
        results.extend(structure_results)
        
        for r in structure_results:
            context_parts.append(f"[STRUCTURE] {r.get('text', '')}")
    
    if route.should_query_details and course_codes and DETAILS_INDEX and DETAILS_INDEX.ntotal > 0:
        details_results = search_details_layer(
            DETAILS_INDEX,
            DETAILS_METAS,
            question,
            course_codes=course_codes,
            top_k=DETAILS_LAYER_TOP_K
        )
        results.extend(details_results)
        
        for r in details_results:
            context_parts.append(f"[DETAILS - {r.get('course_code', 'N/A')}] {r.get('text', '')}")
    
    if not context_parts and GLOBAL_INDEX and GLOBAL_METAS:
        reflection = await REFLECTION_AGENT.reflect(question, trace)
        retrieval = RETRIEVER_AGENT.retrieve(
            GLOBAL_INDEX,
            GLOBAL_METAS,
            reflection["retrieval_query"],
            trace,
        )
        context = retrieval["context"]
    else:
        context = "\n\n".join(context_parts[:MAX_CONTEXT_CHUNKS])
    
    response = await CHATBOT_AGENT.answer(
        question,
        trace,
        context=context,
        use_context=True if context else False,
    )
    
    evaluation = await REFLECTION_AGENT.evaluate(
        question,
        response["answer"],
        context,
        trace,
    )
    
    if evaluation["should_rerun"]:
        response = await CHATBOT_AGENT.answer(
            question,
            trace,
            context=context,
            use_context=True,
        )

    await SESSION_MANAGER.add_conversation_pair(user_id, question, response["answer"])
    
    SESSION_MANAGER.add_to_history(user_id, "user", question)
    SESSION_MANAGER.add_to_history(user_id, "assistant", response["answer"])
    
    if route.query_type == "STRUCTURE_ONLY":
        SESSION_MANAGER.update_session(user_id, {"mode": "STRUCTURE"})
    elif route.query_type == "DETAILS_ONLY":
        SESSION_MANAGER.update_session(user_id, {"mode": "DETAILS"})
    
    save_message(user_id, "assistant", response["answer"])
    
    memory_status = SESSION_MANAGER.get_memory_status(user_id)
    
    from app.services.unanswered_detector import is_unanswered, get_uncertainty_reason
    from app.repositories.unanswered_repo import save_unanswered_question
    
    is_low_confidence, confidence_score = is_unanswered(
        answer=response["answer"],
        context=context,
        rag_results_count=len(results)
    )
    
    if is_low_confidence:
        try:
            uncertainty_reason = get_uncertainty_reason(response["answer"], len(results))
            save_unanswered_question(
                question=question,
                attempted_answer=response["answer"],
                confidence_score=confidence_score,
                rag_results_count=len(results),
                uncertainty_reason=uncertainty_reason,
                user_id=user_id
            )
        except Exception as e:
            print(f"Failed to save unanswered question: {e}")
    
    return {
        "answer": response["answer"],
        "trace": trace.to_dict(),
        "metadata": {
            "programme": session.programme,
            "query_type": route.query_type,
            "target_layer": route.target_layer,
            "course_codes": course_codes,
            "results_count": len(results)
        },
        "memory": memory_status
    }


@router.post("/session/reset")
async def reset_session(user_id: str):
    """Reset user session and clear conversation memory."""
    initialize_new_rag_system()
    SESSION_MANAGER.clear_session(user_id)
    return {"status": "reset", "user_id": user_id}


@router.get("/session/status")
async def get_session_status(user_id: str):
    """Get session status."""
    initialize_new_rag_system()
    session = SESSION_MANAGER.get_session(user_id)
    return {
        "user_id": user_id,
        "programme": session.programme,
        "current_term": session.current_term,
        "mode": session.mode,
        "history_count": len(session.history)
    }


@router.get("/session/memory")
async def get_memory_status(user_id: str):
    """Get conversation memory status for UI display."""
    initialize_new_rag_system()
    memory_status = SESSION_MANAGER.get_memory_status(user_id)
    return memory_status


@router.get("/session/summary")
async def get_conversation_summary(user_id: str):
    """Get conversation summary if available."""
    initialize_new_rag_system()
    session = SESSION_MANAGER.get_session(user_id)
    window = session.conversation_window
    
    return {
        "summary": window.summary,
        "pairs_count": len(window.pairs),
        "summarized_count": window.summarized_pair_count,
        "total_pairs": window.summarized_pair_count + len(window.pairs)
    }
