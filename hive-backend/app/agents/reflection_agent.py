import json
from typing import Any
from app.agents.chatbot_agent import FALLBACK_ANSWER
from app.agents.trace import Trace
from app.llm.deepseek import deepseek_chat


class ReflectionAgent:
    async def reflect(self, question: str, trace: Trace) -> dict[str, Any]:
        """
        Decides if we should use RAG context or not.
        """
        messages = [
            {"role": "system", "content": (
                "You are the Reflection Agent. Decide if the user's query requires retrieving information from the university knowledge base.\n"
                "Return valid JSON: {\"use_context\": true/false, \"search_query\": \"refined keywords\"}\n"
                "- use_context: true for queries about courses, prerequisites, credits, failure, planning, or rules.\n"
                "- use_context: false for greetings, or simple chitchat.\n"
            )},
            {"role": "user", "content": question}
        ]

        use_context = False
        search_query = question
        
        try:
            raw = await deepseek_chat(messages, temperature=0.0)
            raw = raw.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            use_context = parsed.get("use_context", False)
            search_query = parsed.get("search_query", question)
        except Exception:
            # Fallback: if we can't decide, default to True to be safe
            use_context = True

        output = {
            "retrieval_query": search_query,
            "use_context": use_context,
        }
        trace.add(
            name="reflection",
            input_data={"question": question},
            output_data=output,
            metadata={"stage": "pre", "llm_routed": True},
        )
        return output

    async def evaluate(
        self,
        question: str,
        answer: str,
        context: str,
        trace: Trace,
    ) -> dict[str, Any]:
        should_rerun = False
        reason = "answer_ok"

        if answer.strip() == FALLBACK_ANSWER.strip() and context.strip():
            should_rerun = True
            reason = "fallback_with_context"

        output = {"should_rerun": should_rerun, "reason": reason}
        trace.add(
            name="reflection",
            input_data={"question": question, "answer": answer},
            output_data=output,
            metadata={"stage": "post"},
        )
        return output
