import datetime

from app.services import daytype


def test_weekday_is_school():
    assert daytype.for_date(datetime.date(2026, 6, 24), {}) == "school"  # Wednesday


def test_weekend_is_weekend():
    assert daytype.for_date(datetime.date(2026, 6, 27), {}) == "weekend"  # Saturday


def test_override_flips_weekday_to_weekend():
    overrides = {datetime.date(2026, 9, 7): "weekend"}  # PyYAML parses dates to date objects
    assert daytype.for_date(datetime.date(2026, 9, 7), overrides) == "weekend"


def test_override_accepts_string_keys():
    assert daytype.for_date(datetime.date(2026, 9, 7), {"2026-09-07": "holiday"}) == "weekend"


def test_override_forces_school_on_weekend():
    # a makeup school day on a Saturday
    overrides = {datetime.date(2026, 6, 27): "school"}
    assert daytype.for_date(datetime.date(2026, 6, 27), overrides) == "school"
