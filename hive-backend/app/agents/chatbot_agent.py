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
        answer = None  # Initialize - will be set by logic or greeting check at end

        if q_low in ["hi", "hello", "hey", "hai", "helo"]:
            answer = "Hi 👋 I’m HIVE, your Intelligent Robotics academic advisor."
            answer_type = "greeting"
        if is_planning_intent(question):
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
                # Check if this is a detailed question (should use RAG) or basic lookup
                detailed_keywords = [
                    "what is",
                    "about",
                    "objective",
                    "assessment",
                    "assess",
                    "content",
                    "topics",
                    "cover",
                    "theory",
                    "practical",
                    "skills",
                    "outcomes",
                    "learning",
                    "lab",
                    "contact hours",
                    "how is",
                    "where in",
                    "pdf",
                    "page"
                ]
                
                is_detailed_question = any(k in q_low for k in detailed_keywords)
                
                # Only use basic course lookup for simple direct queries
                if not is_detailed_question:
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
                            # Check if LLM is enabled
                            from app.core.config import settings
                            
                            if not settings.USE_LLM:
                                # NO-LLM MODE: Extract answer from RAG context
                                # Context format: "[DETAILS - COURSE_CODE] answer text"
                                # or from QA pairs with "answer" field
                                
                                import re
                                import json
                                
                                answer = None
                                
                                # Try to extract from structured context
                                lines = context.split('\n\n')
                                for chunk in lines:
                                    chunk = chunk.strip()
                                    if not chunk:
                                        continue
                                    
                                    # Pattern 1: [DETAILS - CODE] answer
                                    if chunk.startswith('[DETAILS'):
                                        # Extract just the answer part after the metadata
                                        match = re.match(r'\[DETAILS[^\]]*\]\s*(.+)', chunk, re.DOTALL)
                                        if match:
                                            answer = match.group(1).strip()
                                            break
                                    
                                    # Pattern 2: Try to parse as JSON (QA pair)
                                    elif chunk.startswith('{'):
                                        try:
                                            data = json.loads(chunk)
                                            if 'answer' in data:
                                                answer = data['answer']
                                                break
                                        except:
                                            pass
                                    
                                    # Pattern 3: Plain text answer (first substantial line)
                                    elif len(chunk) > 20 and not chunk.startswith('[') and not chunk.startswith('#'):
                                        answer = chunk
                                        break
                                
                                # Fallback to first 300 chars if no answer found
                                if not answer:
                                    answer = context[:300] + "..." if len(context) > 300 else context
                                    if not answer.strip():
                                        answer = "I don't have information about that in my knowledge base."
                                
                                answer_type = "rag_direct"
                            else:
                                # LLM MODE: Generate with DeepSeek
                                from app.llm.deepseek import deepseek_chat
                                
                                msgs = [
                                    {
                                        "role": "system",
                                        "content": """# ROLE
You are HIVE, MMU Engineering Faculty's academic advisor AI.

# CRITICAL CONSTRAINT - CONTEXT ONLY
⚠️ ABSOLUTE RULE: Answer ONLY from the provided context below.
⚠️ If the context doesn't contain the answer, respond EXACTLY: "I don't have that information in my knowledge base."
⚠️ NEVER use outside knowledge, even if you know the answer.
⚠️ NEVER make assumptions or infer information not explicitly stated in context.

# INSTRUCTIONS
1. Read the context carefully
2. Find the exact answer in the context
3. Respond in 1-3 concise sentences
4. Use course codes when mentioned in context (e.g., AAC6133)
5. If programme unclear, ask: "Which programme? (1) Applied AI or (2) Intelligent Robotics?"

# OUTPUT FORMAT
- Direct factual answer from context
- NO emojis
- NO elaboration beyond context
- NO bullet points unless listing items from context

# EXAMPLES

Context: "Q: What is AAC6133 about? A: Responsible AI development, governance frameworks."
Q: What is AAC6133 about?
A: AAC6133 covers responsible AI development and governance frameworks.

Context: "Q: Prerequisites for ACE6313? A: AMT6113 and ACE6113"
Q: What are the prerequisites for ACE6313?
A: ACE6313 requires AMT6113 and ACE6113 as prerequisites.

Context: "Q: Year 1 courses? A: AMT6113, ACE6113"
Q: What about Year 2 courses?
A: I don't have that information in my knowledge base."""
                                    },
                                    {
                                        "role": "user",
                                        "content": f"Context:\n{context}\n\nStudent Question: {question}"
                                    }
                                ]
                                try:
                                    answer = await deepseek_chat(msgs, temperature=0.35)
                                    answer_type = "retrieval_generation"
                                except Exception:
                                    answer = "I'm having trouble connecting to my brain. Please try again."
                                    answer_type = "error"
                        else:
                            answer = FALLBACK_ANSWER
                            answer_type = "fallback"
                else:
                    # Detailed question - ALWAYS use RAG
                    if use_context and context:
                        # Check if LLM is enabled
                        from app.core.config import settings
                        
                        if not settings.USE_LLM:
                            # NO-LLM MODE: Extract answer from RAG context
                            import re
                            import json
                            
                            answer = None
                            
                            # Try to extract from structured context
                            lines = context.split('\n\n')
                            for chunk in lines:
                                chunk = chunk.strip()
                                if not chunk:
                                    continue
                                
                                # Pattern 1: [DETAILS - CODE] answer
                                if chunk.startswith('[DETAILS'):
                                    match = re.match(r'\[DETAILS[^\]]*\]\s*(.+)', chunk, re.DOTALL)
                                    if match:
                                        answer = match.group(1).strip()
                                        break
                                
                                # Pattern 2: Try to parse as JSON (QA pair)
                                elif chunk.startswith('{'):
                                    try:
                                        data = json.loads(chunk)
                                        if 'answer' in data:
                                            answer = data['answer']
                                            break
                                    except:
                                        pass
                                
                                # Pattern 3: Plain text answer
                                elif len(chunk) > 20 and not chunk.startswith('[') and not chunk.startswith('#'):
                                    answer = chunk
                                    break
                            
                            if not answer:
                                answer = context[:300] + "..." if len(context) > 300 else context
                                if not answer.strip():
                                    answer = "I don't have information about that in my knowledge base."
                            
                            answer_type = "rag_direct"
                        else:
                            # LLM MODE: Generate with DeepSeek
                            from app.llm.deepseek import deepseek_chat
                            
                            msgs = [
                                {
                                    "role": "system",
                                    "content": """# ROLE
You are HIVE, MMU Engineering Faculty's academic advisor AI.

# CRITICAL CONSTRAINT - CONTEXT ONLY
⚠️ ABSOLUTE RULE: Answer ONLY from the provided context below.
⚠️ If the context doesn't contain the answer, respond EXACTLY: "I don't have that information in my knowledge base."
⚠️ NEVER use outside knowledge, even if you know the answer.
⚠️ NEVER make assumptions or infer information not explicitly stated in context.

# INSTRUCTIONS
1. Read the context carefully
2. Find the exact answer in the context
3. Respond in 1-3 concise sentences
4. Use course codes when mentioned in context (e.g., AAC6133)
5. If programme unclear, ask: "Which programme? (1) Applied AI or (2) Intelligent Robotics?"

# OUTPUT FORMAT
- Direct factual answer from context
- NO emojis
- NO elaboration beyond context
- NO bullet points unless listing items from context

# EXAMPLES

Context: "Q: What is AAC6133 about? A: Responsible AI development, governance frameworks."
Q: What is AAC6133 about?
A: AAC6133 covers responsible AI development and governance frameworks.

Context: "Q: Prerequisites for ACE6313? A: AMT6113 and ACE6113"
Q: What are the prerequisites for ACE6313?
A: ACE6313 requires AMT6113 and ACE6113 as prerequisites.

Context: "Q: Year 1 courses? A: AMT6113, ACE6113"
Q: What about Year 2 courses?
A: I don't have that information in my knowledge base."""
                                },
                                {
                                    "role": "user",
                                    "content": f"Context:\n{context}\n\nStudent Question: {question}"
                                }
                            ]
                            try:
                                answer = await deepseek_chat(msgs, temperature=0.35)
                                answer_type = "retrieval_generation"
                            except Exception:
                                answer = "I'm having trouble connecting to my brain. Please try again."
                                answer_type = "error"
                    else:
                        answer = FALLBACK_ANSWER
                        answer_type = "fallback"
        
        # PRIORITY FIX: Check for greeting AFTER all RAG/context checks
        # This ensures course questions get answers even on fresh page loads
        if not answer or answer == FALLBACK_ANSWER:
            if q_low in ["hi", "hello", "hey", "hai", "helo"]:
                answer = "Hi 👋 I'm HIVE, your Intelligent Robotics academic advisor."
                answer_type = "greeting"

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
