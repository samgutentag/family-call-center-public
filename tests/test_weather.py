from unittest.mock import patch, MagicMock

import config
from app.services import weather_gov


def _resp(json_body):
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = json_body
    return m


def setup_function():
    weather_gov._forecast_url = None  # reset per-process cache


def test_formats_forecast(monkeypatch):
    monkeypatch.setattr(config.Config, "WEATHER_LAT", "34.0", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_LON", "-119.0", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_PLACE_NAME", "Testville", raising=False)
    points = _resp({"properties": {"forecast": "https://api.weather.gov/grid/forecast"}})
    forecast = _resp({"properties": {"periods": [
        {"name": "This Afternoon", "shortForecast": "Sunny", "temperature": 72},
        {"name": "Tonight", "shortForecast": "Clear", "temperature": 58},
    ]}})
    with patch("app.services.weather_gov.requests.get", side_effect=[points, forecast]):
        line = weather_gov.get_forecast()
    assert "Testville" in line
    assert "72" in line
    assert "58" in line


def test_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.setattr(config.Config, "WEATHER_LAT", "", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_LON", "", raising=False)
    with patch("app.services.weather_gov.requests.get") as get:
        assert weather_gov.get_forecast() is None
    get.assert_not_called()


def test_returns_none_on_failure(monkeypatch):
    monkeypatch.setattr(config.Config, "WEATHER_LAT", "34.0", raising=False)
    monkeypatch.setattr(config.Config, "WEATHER_LON", "-119.0", raising=False)
    with patch("app.services.weather_gov.requests.get", side_effect=RuntimeError("boom")):
        assert weather_gov.get_forecast() is None


def test_weather_route_speaks_forecast_and_notifies(client):
    with patch("app.routes.weather.weather_gov.get_forecast", return_value="It is sunny."), \
         patch("app.routes.weather.pushover.send_notification") as notify:
        resp = client.post("/weather", data={"From": "+15551234567"})
    body = resp.get_data(as_text=True)
    assert "It is sunny." in body
    assert "/call" in body  # redirects back to menu
    notify.assert_called_once()


def test_weather_route_fallback_when_forecast_none(client):
    with patch("app.routes.weather.weather_gov.get_forecast", return_value=None), \
         patch("app.routes.weather.pushover.send_notification"):
        resp = client.post("/weather", data={"From": "+1"})
    assert "can't get the weather" in resp.get_data(as_text=True).lower()


def test_weather_route_survives_pushover_failure(client):
    with patch("app.routes.weather.weather_gov.get_forecast", return_value="Sunny."), \
         patch("app.routes.weather.pushover.send_notification", side_effect=RuntimeError("x")):
        resp = client.post("/weather", data={"From": "+1"})
    assert resp.status_code == 200
    assert "Sunny." in resp.get_data(as_text=True)
