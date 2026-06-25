def _outfit(day_high, bands):
    for band in bands:
        if day_high <= band["up_to"]:
            return band["outfit"]
    return bands[-1]["outfit"]


def build_instruction(forecast, day_type, rules):
    """Compose the spoken instruction: outfit and reminders first, weather last."""
    th = rules["thresholds"]
    bands = rules["rules"][day_type]["bands"]

    clauses = [_outfit(forecast["day_high"], bands)]
    if (forecast["morning_high"] < th["morning_jacket_below"]
            or forecast["afternoon_high"] - forecast["morning_high"] >= th["morning_jacket_delta"]):
        clauses.append("take a jacket for the morning, it warms up later")
    if forecast["uv_max"] > th["uv"]:
        clauses.append("put on sunscreen")
    if forecast["rain_chance"] >= th["rain_probability"]:
        clauses.append("bring your rain jacket")

    instruction = clauses[0] + " today"
    if len(clauses) > 1:
        instruction += ", " + ", ".join(clauses[1:])
    tail = (f" This afternoon it's {forecast['afternoon_high']} and {forecast['conditions']}, "
            f"{forecast['morning_high']} this morning.")
    return instruction + "." + tail
