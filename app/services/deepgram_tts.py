import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

SPEAK_URL = "https://api.deepgram.com/v1/speak"


def synthesize(text, model=None):
    """Return mp3 bytes for `text` from Deepgram Aura, or None if unconfigured
    or on any error (callers fall back to Twilio <Say>)."""
    if not Config.DEEPGRAM_API_KEY:
        return None
    try:
        resp = requests.post(
            SPEAK_URL,
            params={"model": model or Config.DEEPGRAM_TTS_MODEL, "encoding": "mp3"},
            headers={
                "Authorization": f"Token {Config.DEEPGRAM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        logger.exception("Deepgram TTS failed")
        return None
