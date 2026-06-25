from unittest.mock import patch, MagicMock

import config
from app.services import deepgram_stt


def _resp(body):
    m = MagicMock()
    m.raise_for_status.return_value = None
    m.json.return_value = body
    return m


def test_unconfigured_returns_none(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "", raising=False)
    with patch("app.services.deepgram_stt.requests.post") as post:
        assert deepgram_stt.transcribe(b"wav") is None
    post.assert_not_called()


def test_returns_transcript(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "k", raising=False)
    body = {"results": {"channels": [{"alternatives": [{"transcript": "hi mom"}]}]}}
    with patch("app.services.deepgram_stt.requests.post", return_value=_resp(body)):
        assert deepgram_stt.transcribe(b"wav") == "hi mom"


def test_no_speech_returns_empty(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "k", raising=False)
    body = {"results": {"channels": [{"alternatives": []}]}}
    with patch("app.services.deepgram_stt.requests.post", return_value=_resp(body)):
        assert deepgram_stt.transcribe(b"wav") == ""


def test_http_error_returns_none(monkeypatch):
    monkeypatch.setattr(config.Config, "DEEPGRAM_API_KEY", "k", raising=False)
    with patch("app.services.deepgram_stt.requests.post", side_effect=RuntimeError("x")):
        assert deepgram_stt.transcribe(b"wav") is None
