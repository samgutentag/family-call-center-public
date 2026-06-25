import datetime
import logging
import threading
import time

from croniter import croniter

from app.services import daytype, open_meteo, wardrobe, weather_cache
from app.utils.yaml_config import load_yaml
from config import Config

logger = logging.getLogger(__name__)


def _rules():
    return load_yaml(Config.WARDROBE_CONFIG) or {}


def refresh(now=None):
    """Fetch, build the instruction, and write the cache. Best-effort."""
    rules = _rules()
    if not rules.get("windows"):
        logger.error("wardrobe.yml missing or has no 'windows'; skipping refresh")
        return
    forecast = open_meteo.get_forecast(rules["windows"])
    if not forecast:
        logger.info("Weather unconfigured; skipping refresh")
        return
    day_type = daytype.for_today()
    instruction = wardrobe.build_instruction(forecast, day_type, rules)
    fetched_at = (now or datetime.datetime.now()).isoformat()
    weather_cache.write(instruction, day_type, fetched_at)
    logger.info("Weather cache refreshed (%s)", day_type)


def next_fire(cron_list, after):
    return min(croniter(expr, after).get_next(datetime.datetime) for expr in cron_list)


def _loop():
    try:
        refresh()  # warm the cache at startup so the first call is fast
    except Exception:
        logger.exception("Initial weather refresh failed")
    while True:
        try:
            schedule = _rules().get("schedule") or []
            if not schedule:
                logger.warning("No refresh schedule configured; scheduler idle")
                time.sleep(60)
                continue
            after = datetime.datetime.now()
            nxt = next_fire(schedule, after)
            time.sleep(max(1, (nxt - after).total_seconds()))
            refresh()
        except Exception:
            logger.exception("Scheduler loop error")
            time.sleep(60)


def start(app=None):
    threading.Thread(target=_loop, daemon=True).start()
    logger.info("Weather scheduler started")
