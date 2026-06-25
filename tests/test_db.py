from app.utils import db


def test_list_recordings_newest_first():
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM recordings")
        conn.commit()
    db.log_recording("2026-06-20T10:00:00+00:00", "+1", 5, "a.wav", 100, "RE1")
    db.log_recording("2026-06-22T10:00:00+00:00", "+2", 9, "b.wav", 200, "RE2")
    rows = db.list_recordings()
    assert rows[0]["filename"] == "b.wav"
    assert rows[1]["filename"] == "a.wav"
    assert set(rows[0].keys()) >= {"id", "created_at", "caller_id", "duration", "filename", "file_size"}


def test_transcript_round_trips():
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM recordings")
        conn.commit()
    db.log_recording(
        "2026-06-24T12:00:00+00:00", "+1", 7, "c.wav", 300, "RE3",
        transcript="hello there"
    )
    rows = db.list_recordings()
    assert rows[0]["transcript"] == "hello there"


def test_transcript_defaults_to_none():
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM recordings")
        conn.commit()
    db.log_recording("2026-06-24T13:00:00+00:00", "+2", 4, "d.wav", 150, "RE4")
    rows = db.list_recordings()
    assert rows[0]["transcript"] is None
