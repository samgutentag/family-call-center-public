import datetime


def _ordinal(day):
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def _outfit(day_high, bands):
    for band in bands:
        if day_high <= band["up_to"]:
            return band["outfit"]
    return bands[-1]["outfit"]


# Map Open-Meteo condition words to scenario buckets in wardrobe.yml.
_CONDITION_BUCKET = {
    "sunny": "sunny", "mostly sunny": "sunny",
    "partly cloudy": "cloudy", "cloudy": "cloudy",
    "foggy": "foggy",
    "drizzly": "rainy", "rainy": "rainy", "showers": "rainy",
    "snowy": "snowy",
    "stormy": "stormy",
}


def _scenario_line(conditions, scenarios, today):
    """Pick a goofy intro line for the weather, rotated by date so it varies
    day to day (deterministic, not random). None if no lines are configured."""
    bucket = _CONDITION_BUCKET.get(conditions, "default")
    lines = scenarios.get(bucket) or scenarios.get("default") or []
    if not lines:
        return None
    return lines[today.toordinal() % len(lines)]


def build_instruction(forecast, day_type, rules, today=None):
    """Warm, kid-friendly weather + outfit as short sentences for a slow read.
    Opens with the date and always speaks both the morning and afternoon temps."""
    today = today or datetime.date.today()
    date_str = f"{today.strftime('%A')}, {today.strftime('%B')} {_ordinal(today.day)}"
    th = rules["thresholds"]
    bands = rules["rules"][day_type]["bands"]

    parts = [f"Good morning! It's {date_str}."]
    goofy = _scenario_line(forecast["conditions"], rules.get("scenarios", {}), today)
    if goofy:
        parts.append(goofy)
    # Dress for the daytime high (when the kid is actually out), not day_high,
    # which can be a late-evening peak hours after school.
    daytime_high = max(forecast["morning_high"], forecast["afternoon_high"])
    parts.append(f"Today is {_outfit(daytime_high, bands)}.")
    if (forecast["morning_high"] < th["morning_jacket_below"]
            or forecast["afternoon_high"] - forecast["morning_high"] >= th["morning_jacket_delta"]):
        parts.append("Take a jacket for the morning, it warms up later.")
    if forecast["uv_max"] > th["uv"]:
        parts.append("And don't forget your sunscreen!")
    if forecast["rain_chance"] >= th["rain_probability"]:
        parts.append("And bring your rain jacket!")
    parts.append(
        f"This morning it's about {forecast['morning_high']} degrees. "
        f"And this afternoon, it'll be about {forecast['afternoon_high']} degrees "
        f"and {forecast['conditions']}."
    )
    return " ".join(parts)
