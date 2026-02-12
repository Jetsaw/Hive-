"""
Unanswered Questions Detection Service

Detects when the bot provides low-confidence or uncertain answers
and flags them for admin review.
"""

from typing import Tuple

PENALTY_UNCERTAIN_PHRASE = 0.4
PENALTY_NO_RAG_RESULTS = 0.3
PENALTY_FEW_RAG_RESULTS = 0.15
PENALTY_SHORT_ANSWER = 0.2
PENALTY_GENERIC_RESPONSE = 0.25

BONUS_COURSE_CODE_MENTIONED = 0.1

MIN_ANSWER_LENGTH = 50
MIN_RAG_RESULTS_THRESHOLD = 2
DEFAULT_CONFIDENCE_THRESHOLD = 0.6

UNCERTAIN_PHRASES = [
    "i don't know",
    "i'm not sure",
    "unclear",
    "cannot find",
    "don't have information",
    "not available",
    "unable to answer",
    "i apologize",
    "sorry, i"
]

GENERIC_PHRASES = [
    "please provide more",
    "could you clarify",
    "need more details",
    "can you specify"
]

COURSE_CODE_PATTERNS = ["ACE", "MPU", "FKE"]


def has_uncertain_phrases(text: str) -> bool:
    """Check if text contains uncertain phrases."""
    return any(phrase in text for phrase in UNCERTAIN_PHRASES)


def has_generic_phrases(text: str) -> bool:
    """Check if text contains generic/vague phrases."""
    return any(phrase in text for phrase in GENERIC_PHRASES)


def has_course_code(text: str) -> bool:
    """Check if text mentions specific course codes."""
    return any(code in text.upper() for code in COURSE_CODE_PATTERNS)

def calculate_confidence(
    answer: str,
    context: str,
    rag_results_count: int
) -> float:
    """
    Calculate confidence score for an answer.
    
    Args:
        answer: The bot's response
        context: Retrieved context from RAG
        rag_results_count: Number of RAG results found
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    score = 1.0
    answer_lower = answer.lower()
    
    if has_uncertain_phrases(answer_lower):
        score -= PENALTY_UNCERTAIN_PHRASE
    
    if rag_results_count == 0:
        score -= PENALTY_NO_RAG_RESULTS
    elif rag_results_count < MIN_RAG_RESULTS_THRESHOLD:
        score -= PENALTY_FEW_RAG_RESULTS
    
    if len(answer) < MIN_ANSWER_LENGTH:
        score -= PENALTY_SHORT_ANSWER
    
    if has_generic_phrases(answer_lower):
        score -= PENALTY_GENERIC_RESPONSE
    
    if has_course_code(answer):
        score += BONUS_COURSE_CODE_MENTIONED
    
    return max(0.0, min(1.0, score))


def is_unanswered(
    answer: str,
    context: str,
    rag_results_count: int,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> Tuple[bool, float]:
    """
    Determine if an answer should be flagged as unanswered.
    
    Args:
        answer: The bot's response
        context: Retrieved context from RAG
        rag_results_count: Number of RAG results found
        threshold: Confidence threshold (default 0.6)
    
    Returns:
        Tuple of (is_unanswered, confidence_score)
    """
    confidence = calculate_confidence(answer, context, rag_results_count)
    return (confidence < threshold, confidence)


def get_uncertainty_reason(answer: str, rag_count: int) -> str:
    """
    Get human-readable reason for low confidence.
    
    Args:
        answer: The bot's response
        rag_count: Number of RAG results
    
    Returns:
        Reason string
    """
    reasons = []
    answer_lower = answer.lower()
    
    if rag_count == 0:
        reasons.append("No relevant information found in knowledge base")
    
    if has_uncertain_phrases(answer_lower):
        reasons.append("Bot expressed uncertainty")
    
    if len(answer) < MIN_ANSWER_LENGTH:
        reasons.append("Answer too short/incomplete")
    
    if has_generic_phrases(answer_lower):
        reasons.append("Bot requested clarification")
    
    return "; ".join(reasons) if reasons else "Low confidence score"

