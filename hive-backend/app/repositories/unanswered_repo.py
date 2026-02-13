"""
Unanswered Questions Repository

Handles database operations for storing and retrieving unanswered questions.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings


def _get_connection():
    """Get database connection."""
    return sqlite3.connect(settings.SQLITE_PATH)


def init_table():
    """Create unanswered_questions table if it doesn't exist."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS unanswered_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            attempted_answer TEXT,
            confidence_score REAL,
            rag_results_count INTEGER,
            uncertainty_reason TEXT,
            user_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            admin_answer TEXT,
            admin_notes TEXT,
            resolved_at DATETIME,
            resolved_by TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_unanswered_question(
    question: str,
    attempted_answer: str,
    confidence_score: float,
    rag_results_count: int,
    uncertainty_reason: str,
    user_id: str
) -> int:
    """
    Save an unanswered question to the database.
    
    Returns:
        ID of the inserted record
    """
    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO unanswered_questions 
        (question, attempted_answer, confidence_score, rag_results_count, 
         uncertainty_reason, user_id, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (question, attempted_answer, confidence_score, rag_results_count,
         uncertainty_reason, user_id, datetime.utcnow().isoformat())
    )
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return question_id


def get_pending_questions(limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get pending unanswered questions."""
    conn = _get_connection()
    cursor = conn.execute(
        """
        SELECT id, question, attempted_answer, confidence_score, 
               rag_results_count, uncertainty_reason, user_id, timestamp, status
        FROM unanswered_questions
        WHERE status = 'pending'
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "question": r[1],
            "attempted_answer": r[2],
            "confidence_score": r[3],
            "rag_results_count": r[4],
            "uncertainty_reason": r[5],
            "user_id": r[6],
            "timestamp": r[7],
            "status": r[8]
        }
        for r in rows
    ]


def get_all_questions(status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Get all questions, optionally filtered by status."""
    conn = _get_connection()
    
    if status:
        cursor = conn.execute(
            """
            SELECT id, question, attempted_answer, confidence_score,
                   rag_results_count, uncertainty_reason, user_id, timestamp, 
                   status, admin_answer, admin_notes, resolved_at
            FROM unanswered_questions
            WHERE status = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (status, limit)
        )
    else:
        cursor = conn.execute(
            """
            SELECT id, question, attempted_answer, confidence_score,
                   rag_results_count, uncertainty_reason, user_id, timestamp,
                   status, admin_answer, admin_notes, resolved_at
            FROM unanswered_questions
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "question": r[1],
            "attempted_answer": r[2],
            "confidence_score": r[3],
            "rag_results_count": r[4],
            "uncertainty_reason": r[5],
            "user_id": r[6],
            "timestamp": r[7],
            "status": r[8],
            "admin_answer": r[9],
            "admin_notes": r[10],
            "resolved_at": r[11]
        }
        for r in rows
    ]


def get_question_by_id(question_id: int) -> Optional[Dict]:
    """Get a specific question by ID."""
    conn = _get_connection()
    cursor = conn.execute(
        """
        SELECT id, question, attempted_answer, confidence_score,
               rag_results_count, uncertainty_reason, user_id, timestamp,
               status, admin_answer, admin_notes, resolved_at, resolved_by
        FROM unanswered_questions
        WHERE id = ?
        """,
        (question_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "id": row[0],
        "question": row[1],
        "attempted_answer": row[2],
        "confidence_score": row[3],
        "rag_results_count": row[4],
        "uncertainty_reason": row[5],
        "user_id": row[6],
        "timestamp": row[7],
        "status": row[8],
        "admin_answer": row[9],
        "admin_notes": row[10],
        "resolved_at": row[11],
        "resolved_by": row[12]
    }


def mark_as_answered(
    question_id: int,
    admin_answer: str,
    admin_notes: str = "",
    resolved_by: str = "admin"
) -> bool:
    """Mark a question as answered."""
    conn = _get_connection()
    conn.execute(
        """
        UPDATE unanswered_questions
        SET status = 'answered',
            admin_answer = ?,
            admin_notes = ?,
            resolved_at = ?,
            resolved_by = ?
        WHERE id = ?
        """,
        (admin_answer, admin_notes, datetime.utcnow().isoformat(), resolved_by, question_id)
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def mark_as_ignored(question_id: int, reason: str = "") -> bool:
    """Mark a question as ignored."""
    conn = _get_connection()
    conn.execute(
        """
        UPDATE unanswered_questions
        SET status = 'ignored',
            admin_notes = ?,
            resolved_at = ?
        WHERE id = ?
        """,
        (reason, datetime.utcnow().isoformat(), question_id)
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def get_stats() -> Dict:
    """Get statistics about unanswered questions."""
    conn = _get_connection()
    cursor = conn.execute(
        """
        SELECT status, COUNT(*) as count
        FROM unanswered_questions
        GROUP BY status
        """
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    stats = {"pending": 0, "answered": 0, "ignored": 0, "total": 0}
    
    for row in rows:
        status, count = row
        stats[status] = count
        stats["total"] += count
    
    return stats


# Initialize table on import
init_table()
