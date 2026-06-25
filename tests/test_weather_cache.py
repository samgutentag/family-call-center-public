from app.services import weather_cache


def test_write_then_read_roundtrips():
    weather_cache.write("wear a coat. It's 40.", "school", "2026-06-24T04:00:00")
    row = weather_cache.read()
    assert row["instruction"] == "wear a coat. It's 40."
    assert row["day_type"] == "school"


def test_write_upserts_single_row():
    weather_cache.write("first", "school", "2026-06-24T04:00:00")
    weather_cache.write("second", "weekend", "2026-06-25T04:00:00")
    row = weather_cache.read()
    assert row["instruction"] == "second"


def test_is_fresh_today_vs_old():
    row = {"instruction": "x", "day_type": "school", "fetched_at": "2026-06-24T04:00:00"}
    assert weather_cache.is_fresh(row, today="2026-06-24") is True
    assert weather_cache.is_fresh(row, today="2026-06-25") is False
    assert weather_cache.is_fresh(None, today="2026-06-24") is False
