from unittest.mock import patch, MagicMock

import config
from app.services import open_meteo

WINDOWS = {"morning": [8, 12], "afternoon": [12, 16]}


def _resp(body):
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = body
    return m


def _payload():
    hours = [f"2026-06-24T{h:02d}:00" for h in range(24)]
    temps = [50 + h for h in range(24)]  # 8am=58, 11am=61, noon=62, 3pm=65
    return {
        "hourly": {"time": hours, "temperature_2m": temps,
                   "uv_index": [0] * 24, "weather_code": [0] * 24},
        "daily": {"time": ["2026-06-24"], "temperature_2m_max": [78.4],
                  "uv_index_max": [7.2], "precipitation_probability_max": [10],
                  "weather_code": [0]},
    }


def test_shapes_forecast(monkeypatch):
    monkeypatch.setattr(config.Config, "WEATHER_LAT", "34.0", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_LON", "-119.0", raising=False)
    with patch("app.services.open_meteo.requests.get", return_value=_resp(_payload())):
        fc = open_meteo.get_forecast(WINDOWS)
    assert fc["day_high"] == 78
    assert fc["morning_high"] == 61   # max of hours 8..11 -> 58,59,60,61
    assert fc["afternoon_high"] == 65  # max of hours 12..15 -> 62,63,64,65
    assert fc["uv_max"] == 7.2
    assert fc["rain_chance"] == 10
    assert fc["conditions"] == "sunny"


def test_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.setattr(config.Config, "WEATHER_LAT", "", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_LON", "", raising=False)
    with patch("app.services.open_meteo.requests.get") as get:
        assert open_meteo.get_forecast(WINDOWS) is None
    get.assert_not_called()


def test_returns_none_on_null_daily(monkeypatch):
    monkeypatch.setattr(config.Config, "WEATHER_LAT", "34.0", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_LON", "-119.0", raising=False)
    body = {
        "hourly": {"time": ["2026-06-24T08:00"], "temperature_2m": [60],
                   "uv_index": [0], "weather_code": [0]},
        "daily": {"time": ["2026-06-24"], "temperature_2m_max": [None],
                  "uv_index_max": [None], "precipitation_probability_max": [0],
                  "weather_code": [0]},
    }
    with patch("app.services.open_meteo.requests.get", return_value=_resp(body)):
        assert open_meteo.get_forecast(WINDOWS) is None
