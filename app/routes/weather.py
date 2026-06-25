import logging

from flask import Blueprint, request
from twilio.twiml.voice_response import VoiceResponse

from app.services import pushover, scheduler, voice, weather_cache
from app.utils.twilio_validator import validate_twilio_request
from app.utils.twiml import error_response, twiml_response
from config import Config

logger = logging.getLogger(__name__)
weather_bp = Blueprint("weather", __name__)


@weather_bp.post("/weather")
@validate_twilio_request
def weather():
    """Speak the cached weather instruction (twice) and notify what was said."""
    caller = request.form.get("From", "unknown")
    try:
        vr = VoiceResponse()
        row = weather_cache.read()
        if not (row and weather_cache.is_fresh(row)):
            try:
                scheduler.refresh()
                row = weather_cache.read()
            except Exception:
                logger.exception("Live weather refresh failed")

        # Notify with exactly what the child heard (the cached text), once,
        # even though the call plays it twice. Best-effort.
        spoken = row["instruction"] if row else voice.WEATHER_FALLBACK
        try:
            pushover.send_notification(
                title="Weather check",
                message=f"Weather check from {caller}:\n\n{spoken}",
            )
        except Exception:
            logger.warning("Pushover weather notify failed", exc_info=True)

        if row:
            voice.speak(vr, row["instruction"])
            voice.speak(vr, row["instruction"])
            voice.speak(vr, voice.WEATHER_GOODBYE)
            vr.hangup()
        else:
            voice.speak(vr, voice.WEATHER_FALLBACK)
            vr.redirect(f"{Config.BASE_URL}/call")
        return twiml_response(vr)
    except Exception:
        logger.exception("Error in /weather")
        return error_response()
