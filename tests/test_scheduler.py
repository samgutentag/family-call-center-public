import datetime
from unittest.mock import patch

from app.services import scheduler, weather_cache


def test_next_fire_picks_soonest():
    after = datetime.datetime(2026, 6, 24, 3, 0, 0)
    nxt = scheduler.next_fire(["0 4 * * *", "0 12 * * *"], after)
    assert nxt == datetime.datetime(2026, 6, 24, 4, 0, 0)


def test_refresh_writes_cache():
    fc = {"day_high": 66, "morning_high": 60, "afternoon_high": 66,
          "uv_max": 3, "rain_chance": 0, "conditions": "sunny"}
    with patch("app.services.scheduler.open_meteo.get_forecast", return_value=fc), \
         patch("app.services.scheduler.daytype.for_today", return_value="school"):
        scheduler.refresh(now=datetime.datetime(2026, 6, 24, 4, 0, 0))
    row = weather_cache.read()
    assert row["day_type"] == "school"
    assert row["fetched_at"].startswith("2026-06-24")
    assert "Today" in row["instruction"]


def test_refresh_skips_when_unconfigured():
    with patch("app.services.scheduler.open_meteo.get_forecast", return_value=None), \
         patch("app.services.scheduler.weather_cache.write") as write:
        scheduler.refresh()
    write.assert_not_called()


def test_refresh_skips_when_windows_missing():
    from unittest.mock import patch
    with patch("app.services.scheduler._rules", return_value={}), \
         patch("app.services.scheduler.open_meteo.get_forecast") as get, \
         patch("app.services.scheduler.weather_cache.write") as write:
        scheduler.refresh()
    get.assert_not_called()
    write.assert_not_called()


def test_refresh_prerenders_audio():
    fc = {"day_high": 66, "morning_high": 60, "afternoon_high": 66,
          "uv_max": 3, "rain_chance": 0, "conditions": "sunny"}
    with patch("app.services.scheduler.open_meteo.get_forecast", return_value=fc), \
         patch("app.services.scheduler.daytype.for_today", return_value="school"), \
         patch("app.services.scheduler.weather_cache.write"), \
         patch("app.services.scheduler.voice.ensure_audio") as ensure:
        scheduler.refresh(now=datetime.datetime(2026, 6, 24, 4, 0, 0))
    ensure.assert_called_once()
