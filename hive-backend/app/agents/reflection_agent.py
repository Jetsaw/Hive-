from __future__ import annotations

from typing import Any

from app.agents.chatbot_agent import FALLBACK_ANSWER
from app.agents.trace import Trace


class ReflectionAgent:
    def reflect(self, question: str, trace: Trace) -> dict[str, Any]:
        output = {
            "retrieval_query": question,
            "use_context": False,
        }
        trace.add(
            name="reflection",
            input_data={"question": question},
            output_data=output,
            metadata={"stage": "pre"},
        )
        return output

    def evaluate(
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
