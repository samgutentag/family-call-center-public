from twilio.twiml.voice_response import VoiceResponse

from config import Config
from app.services import voice


def twiml_response(vr):
    """Return a Flask response with correct Content-Type for TwiML."""
    from flask import Response

    return Response(str(vr), mimetype="text/xml")


def error_response(message=None):
    """Return a friendly TwiML error that redirects back to the main menu."""
    vr = VoiceResponse()
    voice.speak(vr, message or voice.GENERIC_ERROR)
    vr.redirect(f"{Config.BASE_URL}/call")
    return twiml_response(vr)


def main_menu_twiml():
    """Build and return the main menu TwiML."""
    vr = VoiceResponse()
    gather = vr.gather(
        num_digits=1, action=f"{Config.BASE_URL}/call/route", method="POST", timeout=10
    )
    voice.speak(gather, voice.MENU_PROMPT)
    # If no input, repeat the menu
    vr.redirect(f"{Config.BASE_URL}/call")
    return twiml_response(vr)
