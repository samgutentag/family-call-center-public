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
    assert body.count(f"/audio/{name}") == 2
    assert "<Hangup />" in body
    assert "<Redirect>" not in body
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
    assert "<Hangup />" in body
    assert "<Redirect>" not in body
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
    body = resp.get_data(as_text=True)
    assert body.count("fresh line.") == 2
    assert "<Hangup />" in body


def test_weather_fallback_when_no_cache(client):
    with patch("app.routes.weather.weather_cache.read", return_value=None), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=False), \
         patch("app.routes.weather.scheduler.refresh", side_effect=RuntimeError("x")), \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    assert "can't check the weather" in resp.get_data(as_text=True).lower()


def test_weather_survives_pushover_failure(client):
    row = {"instruction": "ok.", "day_type": "school", "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", return_value=row), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=True), \
         patch("app.routes.weather.pushover.send_notification", side_effect=RuntimeError("x")):
        resp = client.post("/weather", data={"From": "+1"})
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert body.count("ok.") == 2
    assert "<Hangup />" in body


def test_weather_refreshes_when_stale_nonempty(client):
    stale = {"instruction": "old line.", "day_type": "school", "fetched_at": "2026-06-20T04:00:00"}
    fresh = {"instruction": "fresh line.", "day_type": "school", "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", side_effect=[stale, fresh]), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=False), \
         patch("app.routes.weather.scheduler.refresh") as refresh, \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    refresh.assert_called_once()
    body = resp.get_data(as_text=True)
    assert body.count("fresh line.") == 2
    assert "<Hangup />" in body


def test_weather_notification_includes_spoken_text(client):
    row = {"instruction": "Good morning! Today is a skort day.", "day_type": "school",
           "fetched_at": "2026-06-24T04:00:00"}
    with patch("app.routes.weather.weather_cache.read", return_value=row), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=True), \
         patch("app.routes.weather.pushover.send_notification") as notify:
        client.post("/weather", data={"From": "+15551234567"})
    msg = notify.call_args.kwargs["message"]
    assert "Good morning! Today is a skort day." in msg
    assert "+15551234567" in msg


def test_weather_notification_reports_fallback(client):
    with patch("app.routes.weather.weather_cache.read", return_value=None), \
         patch("app.routes.weather.weather_cache.is_fresh", return_value=False), \
         patch("app.routes.weather.scheduler.refresh", side_effect=RuntimeError("x")), \
         patch("app.routes.weather.pushover.send_notification") as notify:
        client.post("/weather", data={"From": "+1"})
    assert "can't check the weather" in notify.call_args.kwargs["message"].lower()
