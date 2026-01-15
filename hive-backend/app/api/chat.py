from fastapi import APIRouter
from pydantic import BaseModel

from app.agents import ChatbotAgent, ReflectionAgent, RetrieverAgent, Trace
from app.memory.repo import save_message

router = APIRouter()

# Global caches for index
GLOBAL_INDEX = None
GLOBAL_METAS = None

CHATBOT_AGENT = ChatbotAgent()
RETRIEVER_AGENT = RetrieverAgent()
REFLECTION_AGENT = ReflectionAgent()


class ChatReq(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
async def chat(req: ChatReq):
    user_id = (req.user_id or "").strip()
    question = (req.message or "").strip()

    if not user_id or not question:
        return {"answer": "Please enter a message."}

    trace = Trace()
    save_message(user_id, "user", question)

    reflection = REFLECTION_AGENT.reflect(question, trace)
    retrieval = RETRIEVER_AGENT.retrieve(
        GLOBAL_INDEX,
        GLOBAL_METAS,
        reflection["retrieval_query"],
        trace,
    )
    response = CHATBOT_AGENT.answer(
        question,
        trace,
        context=retrieval["context"],
        use_context=reflection["use_context"],
    )

    evaluation = REFLECTION_AGENT.evaluate(
        question,
        response["answer"],
        retrieval["context"],
        trace,
    )
    if evaluation["should_rerun"]:
        response = CHATBOT_AGENT.answer(
            question,
            trace,
            context=retrieval["context"],
            use_context=True,
        )

    save_message(user_id, "assistant", response["answer"])
    return {"answer": response["answer"], "trace": trace.to_dict()}
