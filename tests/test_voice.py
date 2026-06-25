import os
from unittest.mock import patch

import config
from app.services import voice
from twilio.twiml.voice_response import VoiceResponse


def test_audio_name_is_deterministic():
    a = voice.audio_name("hello", "aura-2-andromeda-en")
    b = voice.audio_name("hello", "aura-2-andromeda-en")
    assert a == b and a.endswith(".mp3")
    assert voice.audio_name("hello", "other-voice") != a


def test_ensure_audio_writes_file_on_synth(monkeypatch, tmp_path):
    monkeypatch.setattr(config.Config, "AUDIO_DIR", str(tmp_path), raising=False)
    with patch("app.services.voice.deepgram_tts.synthesize", return_value=b"ID3xx"):
        name = voice.ensure_audio("hello world")
    assert name and os.path.exists(os.path.join(str(tmp_path), name))


def test_ensure_audio_returns_none_when_synth_none(monkeypatch, tmp_path):
    monkeypatch.setattr(config.Config, "AUDIO_DIR", str(tmp_path), raising=False)
    with patch("app.services.voice.deepgram_tts.synthesize", return_value=None):
        assert voice.ensure_audio("hello") is None


def test_speak_plays_when_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(config.Config, "AUDIO_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(config.Config, "BASE_URL", "https://x.example", raising=False)
    name = voice.audio_name("hi there")
    with open(os.path.join(str(tmp_path), name), "wb") as f:
        f.write(b"mp3")  # non-empty: a real cache hit
    vr = VoiceResponse()
    voice.speak(vr, "hi there")
    body = str(vr)
    assert "<Play>" in body
    assert f"https://x.example/audio/{name}" in body
    assert "<Say>" not in body


def test_speak_falls_back_to_say(monkeypatch, tmp_path):
    monkeypatch.setattr(config.Config, "AUDIO_DIR", str(tmp_path), raising=False)
    vr = VoiceResponse()
    voice.speak(vr, "uncached text")
    body = str(vr)
    assert "<Say>" in body
    assert "uncached text" in body
    assert "<Play>" not in body


def test_zero_byte_file_is_not_cached(monkeypatch, tmp_path):
    """A 0-byte mp3 (failed write or test stub) must NOT be played."""
    monkeypatch.setattr(config.Config, "AUDIO_DIR", str(tmp_path), raising=False)
    name = voice.audio_name("empty one")
    open(os.path.join(str(tmp_path), name), "wb").close()  # 0 bytes
    vr = VoiceResponse()
    voice.speak(vr, "empty one")
    body = str(vr)
    assert "<Say>" in body
    assert "<Play>" not in body


def test_warm_static_prompts_covers_all(monkeypatch):
    import config
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "k", raising=False)
    with patch("app.services.voice.ensure_audio") as ensure:
        voice.warm_static_prompts()
    assert ensure.call_count == len(voice.STATIC_PROMPTS)
