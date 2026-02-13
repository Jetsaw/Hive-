"""
Smart Suggestions API
Generate context-aware follow-up question suggestions
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import re

router = APIRouter(prefix="/api", tags=["suggestions"])

# Intent categories and their follow-up suggestions
INTENT_SUGGESTIONS = {
    "greeting": [
        "What courses are available in Year 1?",
        "Tell me about the Applied AI programme",
        "What's the difference between AI and Robotics?",
    ],
    "course_selection": [
        "What are the prerequisites for this course?",
        "How many credit hours is this course?",
        "What is the assessment method?",
    ],
    "course_structure": [
        "Show me Year 1 subjects",
        "How many credit hours do I need?",
        "What are the MPU requirements?",
    ],
    "subject_info": [
        "What topics does this course cover?",
        "Is there a lab component?",
        "What's the assessment breakdown?",
    ],
    "prerequisites": [
        "Can I take this without the prerequisite?",
        "What year is this course offered?",
        "What are the co-requisites?",
    ],
    "academic_planning": [
        "What electives should I take?",
        "How do I plan my course load?",
        "When should I take industrial training?",
    ],
    "electives": [
        "What electives are available?",
        "Can I take electives from another programme?",
        "How many elective credits do I need?",
    ],
    "mpu": [
        "Which MPU courses are required?",
        "When should I complete MPU courses?",
        "How many MPU credit hours do I need?",
    ],
    "fyp": [
        "When does FYP start?",
        "What are the FYP requirements?",
        "How is FYP assessed?",
    ],
    "industrial_training": [
        "When is industrial training?",
        "How long is the industrial training?",
        "What companies accept interns?",
    ],
    "credit_hours": [
        "What's the maximum course load per trimester?",
        "How many total credits for graduation?",
        "Can I take extra courses?",
    ],
    "graduation": [
        "What's the minimum CGPA to graduate?",
        "How many credits do I need?",
        "What are the graduation requirements?",
    ],
    "comparison": [
        "What career paths does each programme offer?",
        "Which programme has more hands-on work?",
        "Can I switch between programmes?",
    ],
}

# Keywords to detect intent
INTENT_KEYWORDS = {
    "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
    "course_selection": ["which course", "should i take", "recommend", "choose"],
    "course_structure": ["structure", "programme structure", "year 1", "year 2", "year 3", "year 4", "trimester"],
    "subject_info": ["what is", "about", "tell me about", "describe", "explain"],
    "prerequisites": ["prerequisite", "pre-requisite", "before taking", "required before"],
    "academic_planning": ["plan", "planning", "schedule", "workload"],
    "electives": ["elective", "optional", "free elective"],
    "mpu": ["mpu", "mata pelajaran umum", "general studies"],
    "fyp": ["fyp", "final year project", "thesis", "capstone"],
    "industrial_training": ["industrial training", "internship", "intern", "practical"],
    "credit_hours": ["credit", "credit hours", "how many credits"],
    "graduation": ["graduate", "graduation", "degree", "complete"],
    "comparison": ["compare", "difference", "vs", "versus", "between"],
}


def detect_intent(question: str) -> str:
    question_lower = question.lower()
    best_intent = "greeting"
    best_score = 0

    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in question_lower)
        if score > best_score:
            best_score = score
            best_intent = intent

    return best_intent


class SuggestionRequest(BaseModel):
    question: str
    answer: Optional[str] = None
    programme: Optional[str] = None


@router.post("/suggestions")
async def get_suggestions(req: SuggestionRequest):
    intent = detect_intent(req.question)
    suggestions = INTENT_SUGGESTIONS.get(intent, INTENT_SUGGESTIONS["greeting"])
    return {
        "intent": intent,
        "suggestions": suggestions[:3],
    }


@router.get("/suggestions/default")
async def get_default_suggestions():
    return {
        "suggestions": [
            "What courses are in Year 1?",
            "Tell me about the Applied AI programme",
            "What are the prerequisites?",
            "Compare AI vs Robotics",
        ]
    }
