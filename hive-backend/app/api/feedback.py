"""
Feedback System API
Collect user ratings and comments
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sqlite3
from app.core.config import settings

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackSubmission(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(default="", max_length=1000)
    helpful: Optional[bool] = None
    user_id: Optional[str] = None
    message_id: Optional[str] = None


def _init_feedback_table():
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            rating INTEGER NOT NULL,
            comment TEXT DEFAULT '',
            helpful INTEGER,
            message_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


_init_feedback_table()


@router.post("")
async def submit_feedback(submission: FeedbackSubmission):
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.execute(
        "INSERT INTO feedback (user_id, rating, comment, helpful, message_id) VALUES (?, ?, ?, ?, ?)",
        (submission.user_id, submission.rating, submission.comment,
         1 if submission.helpful else 0 if submission.helpful is not None else None,
         submission.message_id),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Feedback submitted successfully"}


@router.get("/stats")
async def get_feedback_stats():
    conn = sqlite3.connect(settings.SQLITE_PATH)
    cur = conn.execute("SELECT COUNT(*), AVG(rating), SUM(CASE WHEN helpful=1 THEN 1 ELSE 0 END) FROM feedback")
    row = cur.fetchone()

    dist_cur = conn.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating")
    distribution = {str(r[0]): r[1] for r in dist_cur.fetchall()}

    recent_cur = conn.execute(
        "SELECT rating, comment, created_at FROM feedback WHERE comment != '' ORDER BY created_at DESC LIMIT 10"
    )
    recent = [{"rating": r[0], "comment": r[1], "date": r[2]} for r in recent_cur.fetchall()]
    conn.close()

    return {
        "total_feedback": row[0] or 0,
        "average_rating": round(row[1] or 0, 2),
        "helpful_count": row[2] or 0,
        "distribution": distribution,
        "recent_comments": recent,
    }
