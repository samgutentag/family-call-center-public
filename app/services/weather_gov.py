import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

USER_AGENT = "family-call-center (personal home project)"
_forecast_url = None


def _get_forecast_url():
    """Resolve and cache the NWS forecast URL for the configured lat/lon."""
    global _forecast_url
    if _forecast_url:
        return _forecast_url
    points = requests.get(
        f"https://api.weather.gov/points/{Config.WEATHER_LAT},{Config.WEATHER_LON}",
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    points.raise_for_status()
    _forecast_url = points.json()["properties"]["forecast"]
    return _forecast_url


def get_forecast():
    """Return a short spoken forecast string, or None on any failure."""
    try:
        if not (Config.WEATHER_LAT and Config.WEATHER_LON):
            logger.info("Weather location not configured; skipping forecast")
            return None
        url = _get_forecast_url()
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        periods = resp.json()["properties"]["periods"]
        place = Config.WEATHER_PLACE_NAME or "your area"
        now = periods[0]
        line = (
            f"In {place}, {now['name'].lower()} will be "
            f"{now['shortForecast'].lower()}, with a temperature around "
            f"{now['temperature']} degrees."
        )
        if len(periods) > 1:
            nxt = periods[1]
            line += (
                f" {nxt['name']}, {nxt['shortForecast'].lower()}, "
                f"around {nxt['temperature']} degrees."
            )
        return line
    except Exception:
        logger.exception("Weather fetch failed")
        return None
