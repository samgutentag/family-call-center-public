import datetime

from app.utils.db import get_connection


def init_cache():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_cache (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                instruction TEXT NOT NULL,
                day_type    TEXT,
                fetched_at  TEXT NOT NULL
            )
            """
        )
        conn.commit()


def write(instruction, day_type, fetched_at):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO weather_cache (id, instruction, day_type, fetched_at)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                instruction = excluded.instruction,
                day_type    = excluded.day_type,
                fetched_at  = excluded.fetched_at
            """,
            (instruction, day_type, fetched_at),
        )
        conn.commit()


def read():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT instruction, day_type, fetched_at FROM weather_cache WHERE id = 1"
        ).fetchone()
        return dict(row) if row else None


def is_fresh(row, today=None):
    if not row:
        return False
    today = today or datetime.date.today().isoformat()
    return str(row["fetched_at"])[:10] == today


init_cache()
