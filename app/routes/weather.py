import logging

from flask import Blueprint, request
from twilio.twiml.voice_response import VoiceResponse

from app.services import pushover, weather_gov
from app.utils.twilio_validator import validate_twilio_request
from app.utils.twiml import error_response, twiml_response
from config import Config

logger = logging.getLogger(__name__)
weather_bp = Blueprint("weather", __name__)


@weather_bp.post("/weather")
@validate_twilio_request
def weather():
    """Notify that the weather was checked, then speak the forecast."""
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
        forecast = weather_gov.get_forecast()
        if forecast:
            vr.say(forecast)
        else:
            vr.say("Sorry, I can't get the weather right now. Please try again later.")
        vr.redirect(f"{Config.BASE_URL}/call")
        return twiml_response(vr)
    except Exception:
        logger.exception("Error in /weather")
        return error_response()
