import sqlite3
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


def init_db():
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
