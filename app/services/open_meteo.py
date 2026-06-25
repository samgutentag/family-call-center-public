import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

URL = "https://api.open-meteo.com/v1/forecast"
USER_AGENT = "family-call-center (personal home project)"

WMO = {
    0: "sunny", 1: "mostly sunny", 2: "partly cloudy", 3: "cloudy",
    45: "foggy", 48: "foggy",
    51: "drizzly", 53: "drizzly", 55: "drizzly",
    61: "rainy", 63: "rainy", 65: "rainy", 66: "rainy", 67: "rainy",
    71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy",
    80: "showers", 81: "showers", 82: "showers",
    95: "stormy", 96: "stormy", 99: "stormy",
}


def _window_high(times, temps, start_hour, end_hour):
    vals = [t for ts, t in zip(times, temps) if start_hour <= int(ts[11:13]) < end_hour]
    return max(vals) if vals else None


def get_forecast(windows):
    """Fetch and shape today's forecast, or None if location is unconfigured."""
    if not (Config.WEATHER_LAT and Config.WEATHER_LON):
        logger.info("Weather location not configured; skipping forecast")
        return None

    params = {
        "latitude": Config.WEATHER_LAT,
        "longitude": Config.WEATHER_LON,
        "hourly": "temperature_2m,uv_index,weather_code",
        "daily": "temperature_2m_max,uv_index_max,precipitation_probability_max,weather_code",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
        "forecast_days": 1,
    }
    resp = requests.get(URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    h, d = data["hourly"], data["daily"]
    if d["temperature_2m_max"][0] is None or d["uv_index_max"][0] is None:
        logger.warning("Open-Meteo returned null daily values; skipping forecast")
        return None
    day_high = d["temperature_2m_max"][0]
    m0, m1 = windows["morning"]
    a0, a1 = windows["afternoon"]
    morning = _window_high(h["time"], h["temperature_2m"], m0, m1)
    afternoon = _window_high(h["time"], h["temperature_2m"], a0, a1)
    return {
        "day_high": round(day_high),
        "morning_high": round(morning if morning is not None else day_high),
        "afternoon_high": round(afternoon if afternoon is not None else day_high),
        "uv_max": d["uv_index_max"][0],
        "rain_chance": d["precipitation_probability_max"][0] or 0,
        "conditions": WMO.get(d["weather_code"][0], "out there"),
    }
