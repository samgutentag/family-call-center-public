import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

LISTEN_URL = "https://api.deepgram.com/v1/listen"


def transcribe(audio_bytes):
    """Transcribe WAV bytes via Deepgram's pre-recorded API.

    Returns the transcript string on success (or "" if no speech was heard),
    or None if unconfigured or on any error — so the caller can report the
    failure explicitly rather than hide it."""
    if not Config.DEEPGRAM_API_KEY or not audio_bytes:
        return None
    try:
        resp = requests.post(
            LISTEN_URL,
            params={"model": Config.DEEPGRAM_STT_MODEL, "smart_format": "true"},
            headers={
                "Authorization": f"Token {Config.DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav",
            },
            data=audio_bytes,
            timeout=30,
        )
        resp.raise_for_status()
        alternatives = resp.json()["results"]["channels"][0]["alternatives"]
        return alternatives[0]["transcript"] if alternatives else ""
    except Exception:
        logger.exception("Deepgram transcription failed")
        return None
