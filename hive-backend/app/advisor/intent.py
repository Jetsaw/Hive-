def is_planning_intent(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "fail", "failed", "retake", "can i take", "eligible", "prereq", "prerequisite",
        "take both", "same semester", "same trimester", "recommend", "plan", "register",
        "subject to take", "what should i take", "next trimester", "course selection"
    ]
    return any(k in t for k in keywords)
