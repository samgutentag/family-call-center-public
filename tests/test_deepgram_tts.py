from unittest.mock import patch, MagicMock

import config
from app.services import deepgram_tts


def test_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "", raising=False)
    with patch("app.services.deepgram_tts.requests.post") as post:
        assert deepgram_tts.synthesize("hello") is None
    post.assert_not_called()


def test_returns_audio_bytes(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "dgkey", raising=False)
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.content = b"ID3mp3bytes"
    with patch("app.services.deepgram_tts.requests.post", return_value=resp) as post:
        out = deepgram_tts.synthesize("hello", model="aura-2-andromeda-en")
    assert out == b"ID3mp3bytes"
    args, kwargs = post.call_args
    assert kwargs["headers"]["Authorization"] == "Token dgkey"
    assert kwargs["params"]["model"] == "aura-2-andromeda-en"
    assert kwargs["params"]["encoding"] == "mp3"
    assert kwargs["json"] == {"text": "hello"}


def test_returns_none_on_http_error(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "dgkey", raising=False)
    with patch("app.services.deepgram_tts.requests.post", side_effect=RuntimeError("boom")):
        assert deepgram_tts.synthesize("hello") is None


def test_apply_rate_noop_at_normal_speed(monkeypatch):
    monkeypatch.setattr(config.Config, "SPEECH_RATE", 1.0, raising=False)
    with patch("app.services.deepgram_tts.subprocess.run") as run:
        assert deepgram_tts._apply_rate(b"audio") == b"audio"
    run.assert_not_called()


def test_apply_rate_invokes_ffmpeg(monkeypatch):
    monkeypatch.setattr(config.Config, "SPEECH_RATE", 0.85, raising=False)
    proc = MagicMock()
    proc.stdout = b"slowed"
    with patch("app.services.deepgram_tts.subprocess.run", return_value=proc) as run:
        out = deepgram_tts._apply_rate(b"audio")
    assert out == b"slowed"
    args, kwargs = run.call_args
    assert "atempo=0.85" in args[0]


def test_apply_rate_falls_back_when_ffmpeg_missing(monkeypatch):
    monkeypatch.setattr(config.Config, "SPEECH_RATE", 0.85, raising=False)
    with patch("app.services.deepgram_tts.subprocess.run", side_effect=FileNotFoundError):
        assert deepgram_tts._apply_rate(b"audio") == b"audio"
