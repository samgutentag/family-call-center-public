import hashlib
import logging
import os
import threading

from app.services import deepgram_tts
from config import Config

logger = logging.getLogger(__name__)

MENU_PROMPT = "Hi there! So glad you called. Press 1 to leave a message. Or press 2 to hear today's weather!"
MENU_REPROMPT = "Oops, I didn't catch that. Press 1 to leave a message. Or press 2 for the weather!"
VOICEMAIL_PROMPT = "Okay! After the beep, tell me your message. When you're all done, press the pound key, or just hang up."
VOICEMAIL_DONE = "Got it! Your message is saved. Talk to you soon. Bye bye!"
WEATHER_FALLBACK = "Hmm, I can't check the weather right now. Try me again in a little while!"
WEATHER_GOODBYE = "Have a great day! Bye bye!"
GENERIC_ERROR = "Oops! Something went wrong. Let's try that again."

STATIC_PROMPTS = [
    MENU_PROMPT, MENU_REPROMPT, VOICEMAIL_PROMPT,
    VOICEMAIL_DONE, WEATHER_FALLBACK, WEATHER_GOODBYE, GENERIC_ERROR,
]


def audio_name(text, model=None):
    model = model or Config.DEEPGRAM_TTS_MODEL
    digest = hashlib.sha256(f"{model}\n{text}".encode("utf-8")).hexdigest()
    # 64 bits is ample for a small, fixed set of prompts; collisions are negligible.
    return f"{digest[:16]}.mp3"


def _cached(path):
    """A cached mp3 is one that exists AND is non-empty. A 0-byte file is a
    failed/truncated write (or a test stub) and must not be served or trusted."""
    return os.path.exists(path) and os.path.getsize(path) > 0


def ensure_audio(text, model=None):
    """Return the cached mp3 filename for `text`, synthesizing it if needed.
    Returns None if Deepgram is unconfigured or synthesis fails."""
    name = audio_name(text, model)
    path = os.path.join(Config.AUDIO_DIR, name)
    if _cached(path):
        return name
    audio = deepgram_tts.synthesize(text, model)
    if not audio:
        return None
    os.makedirs(Config.AUDIO_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(audio)
    os.replace(tmp, path)
    return name


def speak(target, text):
    """Append a <Play> of the cached Deepgram mp3, or fall back to <Say>.
    Never calls Deepgram (no in-call latency); only plays what is cached."""
    name = audio_name(text)
    if _cached(os.path.join(Config.AUDIO_DIR, name)):
        target.play(f"{Config.BASE_URL}/audio/{name}")
    else:
        target.say(text)


def warm_static_prompts():
    """Best-effort pre-render of the fixed prompts. No-op without Deepgram."""
    for text in STATIC_PROMPTS:
        try:
            ensure_audio(text)
        except Exception:
            logger.warning("Failed to warm prompt audio", exc_info=True)


def start_warmup():
    """Warm the static prompt audio in the background so app boot never blocks."""
    threading.Thread(target=warm_static_prompts, daemon=True).start()
