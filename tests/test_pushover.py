from unittest.mock import patch, MagicMock

import config
from app.services import pushover


def test_skips_when_unconfigured(monkeypatch):
    monkeypatch.setattr(config.Config, "PUSHOVER_TOKEN", "", raising=False)
    monkeypatch.setattr(config.Config, "PUSHOVER_USER", "", raising=False)
    with patch("app.services.pushover.requests.post") as post:
        result = pushover.send_notification("t", "m")
    assert result is False
    post.assert_not_called()


def test_posts_expected_fields(monkeypatch):
    monkeypatch.setattr(config.Config, "PUSHOVER_TOKEN", "tok", raising=False)
    monkeypatch.setattr(config.Config, "PUSHOVER_USER", "usr", raising=False)
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    with patch("app.services.pushover.requests.post", return_value=resp) as post:
        result = pushover.send_notification("Hi", "Body", url="http://x/", url_title="Open")
    assert result is True
    args, kwargs = post.call_args
    sent = kwargs["data"]
    assert sent["token"] == "tok"
    assert sent["user"] == "usr"
    assert sent["title"] == "Hi"
    assert sent["message"] == "Body"
    assert sent["url"] == "http://x/"
    assert sent["url_title"] == "Open"
