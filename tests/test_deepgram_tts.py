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
