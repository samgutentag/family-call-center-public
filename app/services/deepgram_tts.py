import logging
import subprocess

import requests

from config import Config

logger = logging.getLogger(__name__)

SPEAK_URL = "https://api.deepgram.com/v1/speak"


def _apply_rate(mp3_bytes):
    """Slow the audio to Config.SPEECH_RATE via ffmpeg atempo (pitch preserved).
    Returns the original bytes unchanged at rate 1.0, or if ffmpeg is missing
    or fails — the call must never break on audio post-processing."""
    rate = Config.SPEECH_RATE
    if not mp3_bytes or rate == 1.0:
        return mp3_bytes
    try:
        proc = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-i", "pipe:0",
             "-filter:a", f"atempo={rate}", "-f", "mp3", "pipe:1"],
            input=mp3_bytes, capture_output=True, timeout=20, check=True,
        )
        return proc.stdout or mp3_bytes
    except (FileNotFoundError, subprocess.SubprocessError):
        logger.warning("ffmpeg unavailable or failed; using normal-speed audio", exc_info=True)
        return mp3_bytes


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
        return _apply_rate(resp.content)
    except Exception:
        logger.exception("Deepgram TTS failed")
        return None
