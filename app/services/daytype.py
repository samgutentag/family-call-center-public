import datetime

from app.utils.yaml_config import load_yaml
from config import Config


def for_date(d, overrides):
    """Return 'school' or 'weekend' for a date, honoring overrides."""
    norm = {}
    for key, val in (overrides or {}).items():
        norm[key.isoformat() if hasattr(key, "isoformat") else str(key)] = val
    val = norm.get(d.isoformat())
    if val:
        return "weekend" if val in ("weekend", "holiday") else "school"
    return "school" if d.weekday() < 5 else "weekend"


def for_today():
    overrides = load_yaml(Config.DAY_OVERRIDES) or {}
    return for_date(datetime.date.today(), overrides)
