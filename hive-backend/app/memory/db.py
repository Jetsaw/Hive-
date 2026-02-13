import sqlite3
import threading
from pathlib import Path
from app.core.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_user_time ON messages(user_id, created_at);
"""


class ConnectionPool:
    """Simple thread-local SQLite connection pool for connection reuse."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()

    def get(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn = conn
        return conn


# Global connection pool
_pool = None


def get_connection() -> sqlite3.Connection:
    """Get a pooled database connection."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(settings.SQLITE_PATH)
    return _pool.get()


def init_db():
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
