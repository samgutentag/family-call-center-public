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
    """Notify the weather was checked, then speak the cached instruction."""
    caller = request.form.get("From", "unknown")
    try:
        pushover.send_notification(
            title="Weather check",
            message=f"Someone checked the weather from {caller}.",
        )
    except Exception:
        logger.warning("Pushover weather notify failed", exc_info=True)

    try:
        vr = VoiceResponse()
        row = weather_cache.read()
        if not (row and weather_cache.is_fresh(row)):
            try:
                scheduler.refresh()
                row = weather_cache.read()
            except Exception:
                logger.exception("Live weather refresh failed")
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
