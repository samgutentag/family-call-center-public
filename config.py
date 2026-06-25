import os
from dotenv import load_dotenv

load_dotenv()


def require_env(key):
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


class Config:
    TWILIO_ACCOUNT_SID = require_env("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = require_env("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = require_env("TWILIO_PHONE_NUMBER")

    BASE_URL = require_env("BASE_URL").rstrip("/")

    DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
    RECORDINGS_DIR = os.path.join(DATA_DIR, "recordings")
    AUDIO_DIR = os.path.join(DATA_DIR, "audio")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
    DEEPGRAM_TTS_MODEL = os.getenv("DEEPGRAM_TTS_MODEL", "aura-2-andromeda-en")
    # Playback speed for synthesized audio (1.0 = normal; <1 slows it down via
    # ffmpeg atempo after synthesis). Requires ffmpeg when not 1.0.
    try:
        SPEECH_RATE = float(os.getenv("SPEECH_RATE") or "1.0")
    except ValueError:
        SPEECH_RATE = 1.0

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    TWILIO_VALIDATION_ENABLED = (
        os.getenv("TWILIO_VALIDATION_ENABLED", "true").lower() == "true"
    )

    PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN", "")
    PUSHOVER_USER = os.getenv("PUSHOVER_USER", "")

    TAILNET_HOSTNAME = os.getenv("TAILNET_HOSTNAME", "")

    WEATHER_LAT = os.getenv("WEATHER_LAT", "")
    WEATHER_LON = os.getenv("WEATHER_LON", "")
    WEATHER_PLACE_NAME = os.getenv("WEATHER_PLACE_NAME", "")

    # `or` (not the getenv default) so an empty value in .env falls back to the
    # repo default rather than resolving to "" and failing to load.
    WARDROBE_CONFIG = os.getenv("WARDROBE_CONFIG") or os.path.join(
        os.path.dirname(__file__), "config", "wardrobe.yml"
    )
    DAY_OVERRIDES = os.getenv("DAY_OVERRIDES") or os.path.join(
        os.path.dirname(__file__), "config", "day_overrides.yml"
    )
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
