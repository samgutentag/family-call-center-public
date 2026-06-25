from app.services import wardrobe

RULES = {
    "thresholds": {"uv": 5, "morning_jacket_below": 55, "morning_jacket_delta": 12,
                   "rain_probability": 40},
    "rules": {
        "school": {"bands": [
            {"up_to": 52, "outfit": "wear pants, a long sleeve, and a jacket"},
            {"up_to": 62, "outfit": "wear pants and a long sleeve"},
            {"up_to": 70, "outfit": "wear your skort and a long sleeve"},
            {"up_to": 999, "outfit": "wear your skort and a t-shirt"},
        ]},
        "weekend": {"bands": [
            {"up_to": 70, "outfit": "wear pants and a t-shirt"},
            {"up_to": 999, "outfit": "wear shorts and a t-shirt"},
        ]},
    },
}


def _fc(day_high=66, morning_high=60, afternoon_high=66, uv_max=3, rain_chance=0, conditions="sunny"):
    return {"day_high": day_high, "morning_high": morning_high, "afternoon_high": afternoon_high,
            "uv_max": uv_max, "rain_chance": rain_chance, "conditions": conditions}


def test_school_band_by_high():
    out = wardrobe.build_instruction(_fc(day_high=66), "school", RULES)
    assert out.startswith("wear your skort and a long sleeve today")


def test_weekend_band_by_high():
    out = wardrobe.build_instruction(_fc(day_high=66), "weekend", RULES)
    assert out.startswith("wear pants and a t-shirt today")


def test_morning_jacket_by_absolute_cold():
    out = wardrobe.build_instruction(_fc(morning_high=50, afternoon_high=58), "school", RULES)
    assert "jacket for the morning" in out


def test_morning_jacket_by_delta():
    out = wardrobe.build_instruction(_fc(morning_high=60, afternoon_high=75), "school", RULES)
    assert "jacket for the morning" in out


def test_no_morning_jacket_when_warm_and_flat():
    out = wardrobe.build_instruction(_fc(morning_high=64, afternoon_high=68), "school", RULES)
    assert "jacket for the morning" not in out


def test_sunscreen_above_uv_threshold():
    assert "sunscreen" in wardrobe.build_instruction(_fc(uv_max=6), "school", RULES)


def test_no_sunscreen_at_threshold():
    assert "sunscreen" not in wardrobe.build_instruction(_fc(uv_max=5), "school", RULES)


def test_rain_jacket_at_threshold():
    assert "rain jacket" in wardrobe.build_instruction(_fc(rain_chance=40), "school", RULES)


def test_band_boundary_is_inclusive():
    # day_high == 62 must pick the up_to:62 band, not the next one
    out = wardrobe.build_instruction(_fc(day_high=62), "school", RULES)
    assert out.startswith("wear pants and a long sleeve today")


def test_weather_tail_is_last():
    out = wardrobe.build_instruction(_fc(afternoon_high=66, morning_high=60, conditions="sunny"), "school", RULES)
    assert out.endswith("66 and sunny, 60 this morning.")
