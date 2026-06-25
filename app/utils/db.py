import sqlite3
import os
from config import Config

DB_PATH = os.path.join(Config.DATA_DIR, "ivr.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL,
                caller_id   TEXT,
                duration    INTEGER,
                filename    TEXT    NOT NULL,
                file_size   INTEGER,
                twilio_sid  TEXT
            )
        """)
        conn.commit()


def log_recording(created_at, caller_id, duration, filename, file_size, twilio_sid):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO recordings (created_at, caller_id, duration, filename, file_size, twilio_sid)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (created_at, caller_id, duration, filename, file_size, twilio_sid),
        )
        conn.commit()


def list_recordings(limit=100):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, caller_id, duration, filename, file_size
            FROM recordings
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
