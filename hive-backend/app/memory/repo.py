import sqlite3
from typing import List, Dict
from app.core.config import settings


def save_message(user_id: str, role: str, content: str) -> None:
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.execute(
        "INSERT INTO messages(user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content),
    )
    conn.commit()
    conn.close()


def get_recent_messages(user_id: str, limit: int = 8) -> List[Dict[str, str]]:
    conn = sqlite3.connect(settings.SQLITE_PATH)
    cur = conn.execute(
        "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()

    rows.reverse()
    return [{"role": r[0], "content": r[1]} for r in rows]
