import os
from unittest.mock import patch

import config
from app.services import voice


def test_weather_plays_cached_instruction(client):
    instruction = "wear shorts. It's 80."
    os.makedirs(config.Config.AUDIO_DIR, exist_ok=True)
    name = voice.audio_name(instruction)
    audio_path = os.path.join(config.Config.AUDIO_DIR, name)
    with open(audio_path, "wb") as f:
        f.write(b"mp3")  # non-empty: a real cache hit
    row = {"instruction": instruction, "day_type": "weekend", "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", return_value=row), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=True), \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    body = resp.get_data(as_text=True)
    assert "<Play>" in body
    assert f"/audio/{name}" in body
    os.remove(audio_path)


def test_weather_speaks_fresh_cache(client):
    row = {"instruction": "wear shorts. It's 80.", "day_type": "weekend",
           "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", return_value=row), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=True), \
         patch("app.routes.weather.scheduler.refresh") as refresh, \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    body = resp.get_data(as_text=True)
    assert "wear shorts. It's 80." in body
    assert "/call" in body
    refresh.assert_not_called()


def test_weather_refreshes_when_stale(client):
    fresh = {"instruction": "fresh line.", "day_type": "school",
             "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", side_effect=[None, fresh]), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=False), \
         patch("app.routes.weather.scheduler.refresh") as refresh, \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    refresh.assert_called_once()
    assert "fresh line." in resp.get_data(as_text=True)


def test_weather_fallback_when_no_cache(client):
    with patch("app.routes.weather.weather_cache.read", return_value=None), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=False), \
         patch("app.routes.weather.scheduler.refresh", side_effect=RuntimeError("x")), \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    assert "can't get the weather" in resp.get_data(as_text=True).lower()


def test_weather_survives_pushover_failure(client):
    row = {"instruction": "ok.", "day_type": "school", "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", return_value=row), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=True), \
         patch("app.routes.weather.pushover.send_notification", side_effect=RuntimeError("x")):
        resp = client.post("/weather", data={"From": "+1"})
    assert resp.status_code == 200
    assert "ok." in resp.get_data(as_text=True)


def test_weather_refreshes_when_stale_nonempty(client):
    stale = {"instruction": "old line.", "day_type": "school", "fetched_at": "2026-06-20T04:00:00"}
    fresh = {"instruction": "fresh line.", "day_type": "school", "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", side_effect=[stale, fresh]), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=False), \
         patch("app.routes.weather.scheduler.refresh") as refresh, \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    refresh.assert_called_once()
    assert "fresh line." in resp.get_data(as_text=True)
