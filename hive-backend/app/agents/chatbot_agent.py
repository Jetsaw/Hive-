from __future__ import annotations

from typing import Any

from app.advisor.intent import is_planning_intent
from app.advisor.engine import (
    load_kb,
    load_faie_kb,
    resolve_course_from_text,
    resolve_course_mentions,
    answer_fail_question,
    recommend_for_trimester,
    extract_course_codes,
    parse_trimester,
)
from app.agents.trace import Trace

FALLBACK_ANSWER = (
    "I can help with prerequisites and planning.\n"
    "Try: “If I fail Math 1, can I take Math 2?” or “Plan Year 1 Sem 2”."
)


class ChatbotAgent:
    def __init__(self) -> None:
        self._course_catalog: dict[str, Any] | None = None
        self._programme_plan: dict[str, Any] | None = None
        self._faie_kb: dict[str, Any] | None = None
        self._faie_code_map: dict[str, Any] | None = None
        self._faie_name_map: dict[str, Any] | None = None

    def _load_kbs(self) -> None:
        if self._course_catalog is None or self._programme_plan is None:
            self._course_catalog, self._programme_plan, _ = load_kb()

        if self._faie_kb is None or self._faie_code_map is None or self._faie_name_map is None:
            self._faie_kb, self._faie_code_map, self._faie_name_map = load_faie_kb()

    async def answer(
        self,
        question: str,
        trace: Trace,
        context: str = "",
        use_context: bool = False,
    ) -> dict[str, Any]:
        self._load_kbs()

        q_low = question.lower()
        answer_type = "fallback"

        if q_low in ["hi", "hello", "hey", "hai", "helo"]:
            answer = "Hi 👋 I’m HIVE, your Intelligent Robotics academic advisor."
            answer_type = "greeting"
        elif is_planning_intent(question):
            passed = extract_course_codes(question) if "passed" in q_low else []
            failed = extract_course_codes(question) if ("failed" in q_low or "fail" in q_low) else []

            trimester_key = parse_trimester(question)
            if trimester_key:
                plan = (self._programme_plan or {}).get("Intelligent Robotics", {})
                
                # Check if the trimester exists in the plan
                if trimester_key not in plan:
                    answer = f"I don't have course information for {trimester_key.replace('_', ' ').replace('T', 'Semester ')}. Please check the year and semester."
                    answer_type = "planning_error"
                else:
                    result = recommend_for_trimester(
                        trimester_key,
                        passed,
                        failed,
                        plan,
                        self._course_catalog or {},
                    )

                    pretty = trimester_key.replace("_", " ").replace("T", "Semester ")
                    
                    if result["recommended"]:
                        rec = "\n".join(f"- {c}" for c in result["recommended"])
                    else:
                        rec = "- (none available)"
                    
                    if result["blocked"]:
                        blk = "\n".join(f"- {c}" for c in result["blocked"])
                    else:
                        blk = "- (none)"

                    answer = f"📚 Recommended courses for {pretty}:\n{rec}\n\n🔒 Not eligible yet:\n{blk}"
                    answer_type = "planning"
            else:
                answer = answer_fail_question(
                    question,
                    passed,
                    failed,
                    self._course_catalog or {},
                )
                answer_type = "planning"
        else:
            advising_keywords = [
                "fail",
                "failed",
                "can i",
                "can i take",
                "prereq",
                "prerequisite",
                "next sem",
                "next semester",
                "eligible",
                "allowed",
                "take both",
                "same semester",
            ]

            if any(k in q_low for k in advising_keywords):
                mentioned = resolve_course_mentions(
                    question,
                    self._faie_code_map or {},
                    self._faie_name_map or {},
                )

                if mentioned:
                    question = question + " " + " ".join(mentioned)

                answer = answer_fail_question(
                    question,
                    [],
                    [],
                    self._course_catalog or {},
                )
                answer_type = "advising"
            else:
                code = resolve_course_from_text(
                    question,
                    self._faie_code_map or {},
                    self._faie_name_map or {},
                )
                if code and code in (self._faie_code_map or {}):
                    c = (self._faie_code_map or {})[code]
                    name = c.get("name", "")
                    credits = c.get("credits", "")
                    prereq = c.get("prerequisite") or c.get("prereq") or []
                    prereq_str = ", ".join(prereq) if prereq else "None"

                    answer = (
                        f"{code} — {name}\nCredits: {credits}\n"
                        f"Prerequisite: {prereq_str}"
                    )
                    answer_type = "course_info"
                else:
                    if use_context and context:
                        # RAG Generation via LLM
                        from app.llm.deepseek import deepseek_chat
                        
                        msgs = [
                            {
                                "role": "system",
                                "content": """You are HIVE, an intelligent academic advisor for MMU Engineering Faculty.

CRITICAL RULES:
1. ALWAYS be concise - maximum 2-3 sentences per response
2. NO emojis in responses
3. If question is about course structure and programme is unclear, ASK which programme first:
   - "Which programme? (1) Applied AI or (2) Intelligent Robotics?"
4. Use bullet points ONLY when listing multiple items
5. If context doesn't have the answer, say "I don't have that information" - don't elaborate

Your role:
- Help with course requirements, prerequisites, and program structures
- Guide academic planning for Intelligent Robotics and Applied AI programs
- Provide accurate, brief answers

Response format:
- Direct answer first
- Course codes when relevant (e.g., ACE6143)
- No unnecessary explanations
- No emojis

Example good responses:
- "ACE6313 requires AMT6113 and ACE6113 as prerequisites."
- "Year 1 Trimester 1 has 5 courses: AMT6113, ACE6113, ALE6113, AHS6113, AEE6113."
- "Which programme? (1) Applied AI or (2) Intelligent Robotics?"

Example bad responses:
- Long paragraphs with multiple explanations
- Responses with emojis like 👋 or 📚
- Answering without clarifying which programme when structure is asked

Context from:
- Course catalog with detailed information
- Program structures for both programmes
- Common Q&A pairs"""
                            },
                            {
                                "role": "user",
                                "content": f"Context:\n{context}\n\nStudent Question: {question}"
                            }
                        ]
                        try:
                            answer = await deepseek_chat(msgs, temperature=0.3)
                            answer_type = "retrieval_generation"
                        except Exception:
                            answer = "I'm having trouble connecting to my brain. Please try again."
                            answer_type = "error"
                    else:
                        answer = FALLBACK_ANSWER
                        answer_type = "fallback"

        trace.add(
            name="chatbot",
            input_data={
                "question": question,
                "use_context": use_context,
                "context_chars": len(context),
            },
            output_data={"answer": answer, "answer_type": answer_type},
        )
        return {"answer": answer, "answer_type": answer_type}
