import datetime

from app.services import wardrobe

RULES = {
    "thresholds": {"uv": 5, "morning_jacket_below": 55, "morning_jacket_delta": 12,
                   "rain_probability": 40},
    "rules": {
        "school": {"bands": [
            {"up_to": 52, "outfit": "a bundle-up day for pants, a long sleeve, and a jacket"},
            {"up_to": 62, "outfit": "a pants and long sleeve day"},
            {"up_to": 70, "outfit": "a skort and long sleeve day"},
            {"up_to": 999, "outfit": "a skort and t-shirt day"},
        ]},
        "weekend": {"bands": [
            {"up_to": 70, "outfit": "a pants and t-shirt day"},
            {"up_to": 999, "outfit": "a shorts and t-shirt day"},
        ]},
    },
    "scenarios": {
        "sunny": ["Sunny day woohoo!", "Here comes the sun!"],
        "rainy": ["Splashy puddle day!"],
        "default": ["What's the sky doing today?"],
    },
}

DATE = datetime.date(2026, 6, 1)


def _fc(day_high=66, morning_high=60, afternoon_high=66, uv_max=3, rain_chance=0, conditions="sunny"):
    return {"day_high": day_high, "morning_high": morning_high, "afternoon_high": afternoon_high,
            "uv_max": uv_max, "rain_chance": rain_chance, "conditions": conditions}


def _build(fc=None, day_type="school"):
    return wardrobe.build_instruction(fc or _fc(), day_type, RULES, today=DATE)


def test_ordinal():
    assert wardrobe._ordinal(1) == "1st"
    assert wardrobe._ordinal(2) == "2nd"
    assert wardrobe._ordinal(3) == "3rd"
    assert wardrobe._ordinal(4) == "4th"
    assert wardrobe._ordinal(11) == "11th"
    assert wardrobe._ordinal(12) == "12th"
    assert wardrobe._ordinal(13) == "13th"
    assert wardrobe._ordinal(21) == "21st"
    assert wardrobe._ordinal(22) == "22nd"
    assert wardrobe._ordinal(23) == "23rd"


def test_speaks_the_date():
    out = _build()
    assert out.startswith("Good morning! It's ")
    assert f"{DATE.strftime('%A')}, June 1st." in out


def test_includes_morning_and_afternoon():
    out = _build(_fc(morning_high=60, afternoon_high=66, conditions="sunny"))
    assert "This morning it's about 60 degrees" in out
    assert "this afternoon, it'll be about 66 degrees and sunny" in out


def test_school_band_by_high():
    assert "Today is a skort and long sleeve day." in _build(_fc(day_high=66))


def test_weekend_band_by_high():
    assert "Today is a pants and t-shirt day." in _build(_fc(day_high=66), "weekend")


def test_band_boundary_is_inclusive():
    assert "Today is a pants and long sleeve day." in _build(_fc(day_high=62))


def test_morning_jacket_by_absolute_cold():
    assert "jacket for the morning" in _build(_fc(morning_high=50, afternoon_high=58))


def test_morning_jacket_by_delta():
    assert "jacket for the morning" in _build(_fc(morning_high=60, afternoon_high=75))


def test_no_morning_jacket_when_warm_and_flat():
    assert "jacket for the morning" not in _build(_fc(morning_high=64, afternoon_high=68))


def test_sunscreen_above_uv_threshold():
    assert "sunscreen" in _build(_fc(uv_max=6))


def test_no_sunscreen_at_threshold():
    assert "sunscreen" not in _build(_fc(uv_max=5))


def test_rain_jacket_at_threshold():
    assert "rain jacket" in _build(_fc(rain_chance=40))


def test_weather_tail_is_last():
    assert _build(_fc(afternoon_high=66, conditions="sunny")).rstrip().endswith(
        "about 66 degrees and sunny."
    )


def test_goofy_line_sits_between_date_and_outfit():
    out = _build(_fc(conditions="sunny"))
    gap = out[out.index("1st.") : out.index("Today is")]
    assert any(line in gap for line in RULES["scenarios"]["sunny"])


def test_goofy_default_for_unmapped_condition():
    out = _build(_fc(conditions="out there"))
    assert RULES["scenarios"]["default"][0] in out


def test_goofy_rotates_by_date():
    fc = _fc(conditions="sunny")
    a = wardrobe.build_instruction(fc, "school", RULES, today=datetime.date(2026, 6, 1))
    b = wardrobe.build_instruction(fc, "school", RULES, today=datetime.date(2026, 6, 2))
    line_a = next(l for l in RULES["scenarios"]["sunny"] if l in a)
    line_b = next(l for l in RULES["scenarios"]["sunny"] if l in b)
    assert line_a != line_b
