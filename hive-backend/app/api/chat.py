from fastapi import APIRouter
from pydantic import BaseModel

from app.memory.repo import save_message
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

router = APIRouter()

# Global caches
COURSE_CATALOG = None
PROGRAMME_PLAN = None

FAIE_KB = None
FAIE_CODE_MAP = None
FAIE_NAME_MAP = None


class ChatReq(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
async def chat(req: ChatReq):
    user_id = (req.user_id or "").strip()
    question = (req.message or "").strip()
    q_low = question.lower()

    if not user_id or not question:
        return {"answer": "Please enter a message."}

    save_message(user_id, "user", question)

    # Load KBs once
    global COURSE_CATALOG, PROGRAMME_PLAN
    if COURSE_CATALOG is None:
        COURSE_CATALOG, PROGRAMME_PLAN, _ = load_kb()

    global FAIE_KB, FAIE_CODE_MAP, FAIE_NAME_MAP
    if FAIE_KB is None:
        FAIE_KB, FAIE_CODE_MAP, FAIE_NAME_MAP = load_faie_kb()

    # ---------- Greeting ----------
    if q_low in ["hi", "hello", "hey", "hai", "helo"]:
        answer = "Hi 👋 I’m HIVE, your Intelligent Robotics academic advisor."
        save_message(user_id, "assistant", answer)
        return {"answer": answer}

    # ---------- Planning ----------
    if is_planning_intent(question):
        passed = extract_course_codes(question) if "passed" in q_low else []
        failed = extract_course_codes(question) if ("failed" in q_low or "fail" in q_low) else []

        trimester_key = parse_trimester(question)
        if trimester_key:
            plan = PROGRAMME_PLAN.get("Intelligent Robotics", {})
            result = recommend_for_trimester(trimester_key, passed, failed, plan, COURSE_CATALOG)

            pretty = trimester_key.replace("_", " ").replace("T", "Sem ")
            rec = "\n".join(f"- {c}" for c in result["recommended"]) or "- (none)"
            blk = "\n".join(f"- {c}" for c in result["blocked"]) or "- (none)"

            answer = f"Recommended for {pretty}:\n{rec}\n\nNot eligible yet:\n{blk}"
            save_message(user_id, "assistant", answer)
            return {"answer": answer}

        answer = answer_fail_question(question, passed, failed, COURSE_CATALOG)
        save_message(user_id, "assistant", answer)
        return {"answer": answer}

    # ---------- Advising / Prerequisite ----------
    advising_keywords = [
        "fail", "failed",
        "can i", "can i take",
        "prereq", "prerequisite",
        "next sem", "next semester",
        "eligible", "allowed",
        "take both", "same semester",
    ]



    if any(k in q_low for k in advising_keywords):
        mentioned = resolve_course_mentions(question, FAIE_CODE_MAP, FAIE_NAME_MAP)
        print("DEBUG mentioned:", mentioned, "question:", question)

        # IMPORTANT: inject resolved codes so answer_fail_question can work
        if mentioned:
            question = question + " " + " ".join(mentioned)

        answer = answer_fail_question(question, [], [], COURSE_CATALOG)
        save_message(user_id, "assistant", answer)
        return {"answer": answer}

    # ---------- Course info ----------
    code = resolve_course_from_text(question, FAIE_CODE_MAP, FAIE_NAME_MAP)
    if code and code in FAIE_CODE_MAP:
        c = FAIE_CODE_MAP[code]
        name = c.get("name", "")
        credits = c.get("credits", "")
        prereq = c.get("prerequisite") or c.get("prereq") or []
        prereq_str = ", ".join(prereq) if prereq else "None"

        answer = f"{code} — {name}\nCredits: {credits}\nPrerequisite: {prereq_str}"
        save_message(user_id, "assistant", answer)
        return {"answer": answer}

    # ---------- Fallback ----------
    answer = (
        "I can help with prerequisites and planning.\n"
        "Try: “If I fail Math 1, can I take Math 2?” or “Plan Year 1 Sem 2”."
    )
    save_message(user_id, "assistant", answer)
    return {"answer": answer}
