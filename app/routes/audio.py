from flask import Blueprint, send_from_directory

from config import Config

audio_bp = Blueprint("audio", __name__)


@audio_bp.get("/audio/<path:filename>")
def serve_audio(filename):
    """Serve a cached prompt/weather mp3 to Twilio. Public on purpose."""
    return send_from_directory(Config.AUDIO_DIR, filename)
