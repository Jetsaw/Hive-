"""
Admin API Endpoints
Provides admin dashboard functionality for monitoring and debugging
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.memory.repo import (
    get_all_conversations,
    get_conversation_history,
    get_recent_messages,
)

router = APIRouter()


class ConversationSummary(BaseModel):
    user_id: str
    message_count: int
    last_message_time: str
    last_message: str


class HealthMetrics(BaseModel):
    status: str
    uptime_seconds: int
    total_conversations: int
    total_messages: int
    voice_enabled: bool


@router.get("/admin/conversations")
async def list_conversations(limit: int = 50) -> List[ConversationSummary]:
    """
    Get list of all user conversations with summary
    
    - **limit**: Maximum number of conversations to return
    """
    try:
        conversations = get_all_conversations(limit)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@router.get("/admin/conversation/{user_id}")
async def get_conversation(user_id: str):
    """
    Get full conversation history for a specific user
    
    - **user_id**: User identifier
    """
    try:
        history = get_conversation_history(user_id)
        return {
            "user_id": user_id,
            "messages": history,
            "count": len(history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")


@router.get("/admin/messages/recent")
async def get_recent(limit: int = 100):
    """
    Get recent messages across all users
    
    - **limit**: Maximum number of messages to return
    """
    try:
        messages = get_recent_messages(limit)
        return {
            "messages": messages,
            "count": len(messages),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


@router.get("/admin/health")
async def get_health() -> HealthMetrics:
    """
    Get system health metrics
    """
    import time
    from app.main import app
    
    # Calculate uptime (simplified - would need proper tracking in production)
    uptime = int(time.time() - getattr(app.state, 'start_time', time.time()))
    
    # Get conversation stats
    conversations = get_all_conversations(limit=10000)
    total_conversations = len(conversations)
    total_messages = sum(c.get('message_count', 0) for c in conversations)
    
    return HealthMetrics(
        status="healthy",
        uptime_seconds=uptime,
        total_conversations=total_conversations,
        total_messages=total_messages,
        voice_enabled=True,
    )


@router.get("/admin/stats")
async def get_stats():
    """
    Get usage statistics
    """
    conversations = get_all_conversations(limit=10000)
    
    # Calculate stats
    total_users = len(conversations)
    total_messages = sum(c.get('message_count', 0) for c in conversations)
    avg_messages_per_user = total_messages / total_users if total_users > 0 else 0
    
    # Most active users
    active_users = sorted(
        conversations,
        key=lambda x: x.get('message_count', 0),
        reverse=True
    )[:10]
    
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "avg_messages_per_user": round(avg_messages_per_user, 2),
        "most_active_users": active_users,
    }


# ===== UNANSWERED QUESTIONS ENDPOINTS =====

from app.repositories import unanswered_repo


class AnswerSubmission(BaseModel):
    answer: str
    notes: str = ""
    add_to_kb: bool = False


class IgnoreRequest(BaseModel):
    reason: str = ""


@router.get("/admin/unanswered")
async def get_unanswered_questions(
    status: Optional[str] = None,
    limit: int = 100
):
    """Get unanswered questions, optionally filtered by status."""
    try:
        questions = unanswered_repo.get_all_questions(status=status, limit=limit)
        stats = unanswered_repo.get_stats()
        
        return {
            "questions": questions,
            "total": len(questions),
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/unanswered/{question_id}")
async def get_question_details(question_id: int):
    """Get details of a specific unanswered question."""
    question = unanswered_repo.get_question_by_id(question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question


@router.post("/admin/unanswered/{question_id}/answer")
async def submit_answer(question_id: int, submission: AnswerSubmission):
    """Submit an answer for an unanswered question."""
    question = unanswered_repo.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    success = unanswered_repo.mark_as_answered(
        question_id=question_id,
        admin_answer=submission.answer,
        admin_notes=submission.notes,
        resolved_by="admin"
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update question")
    
    return {
        "success": True,
        "message": "Answer submitted successfully",
        "question_id": question_id
    }


@router.post("/admin/unanswered/{question_id}/ignore")
async def ignore_question(question_id: int, request: IgnoreRequest):
    """Mark a question as ignored."""
    question = unanswered_repo.get_question_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    success = unanswered_repo.mark_as_ignored(
        question_id=question_id,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update question")
    
    return {
        "success": True,
        "message": "Question marked as ignored",
        "question_id": question_id
    }

