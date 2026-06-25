import os
import pytest
from flask import Flask
from unittest.mock import patch

import config
from app.utils.tailnet import require_tailnet


@pytest.fixture()
def gate_app(monkeypatch):
    monkeypatch.setattr(config.Config, "TAILNET_HOSTNAME", "pi.tailtest.ts.net", raising=False)
    app = Flask(__name__)

    @app.get("/secret")
    @require_tailnet
    def secret():
        return "ok"

    return app


def test_tailnet_host_allowed(gate_app):
    c = gate_app.test_client()
    resp = c.get("/secret", headers={"Host": "pi.tailtest.ts.net"})
    assert resp.status_code == 200


def test_funnel_host_404(gate_app):
    c = gate_app.test_client()
    resp = c.get("/secret", headers={"Host": "funnel.example.ts.net"})
    assert resp.status_code == 404


def test_empty_hostname_fails_closed(monkeypatch):
    monkeypatch.setattr(config.Config, "TAILNET_HOSTNAME", "", raising=False)
    app = Flask(__name__)

    @app.get("/secret")
    @require_tailnet
    def secret():
        return "ok"

    c = app.test_client()
    assert c.get("/secret", headers={"Host": "anything.example.com"}).status_code == 404


def test_host_port_is_stripped(monkeypatch):
    monkeypatch.setattr(config.Config, "TAILNET_HOSTNAME", "pi.tailtest.ts.net", raising=False)
    app = Flask(__name__)

    @app.get("/secret")
    @require_tailnet
    def secret():
        return "ok"

    c = app.test_client()
    assert c.get("/secret", headers={"Host": "pi.tailtest.ts.net:5000"}).status_code == 200


TAILNET = {"Host": "pi.tailtest.ts.net"}
FUNNEL = {"Host": "funnel.example.ts.net"}


def test_inbox_lists_recordings_on_tailnet(client):
    rows = [{"id": 1, "created_at": "2026-06-22T10:00:00+00:00", "caller_id": "+1",
             "duration": 9, "filename": "2026/06/22/b.wav", "file_size": 200}]
    with patch("app.routes.inbox.list_recordings", return_value=rows):
        resp = client.get("/", headers=TAILNET)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "<audio" in body
    assert "/recordings/2026/06/22/b.wav" in body


def test_inbox_404_over_funnel(client):
    resp = client.get("/", headers=FUNNEL)
    assert resp.status_code == 404


def test_serve_recording_on_tailnet(client, app):
    rec_dir = app.config.get("RECORDINGS_DIR") or os.environ["DATA_DIR"] + "/recordings"
    target = os.path.join(os.environ["DATA_DIR"], "recordings", "2026", "06", "22")
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, "b.wav"), "wb") as f:
        f.write(b"RIFFfake")
    resp = client.get("/recordings/2026/06/22/b.wav", headers=TAILNET)
    assert resp.status_code == 200
    assert resp.data == b"RIFFfake"


def test_serve_recording_404_over_funnel(client):
    resp = client.get("/recordings/2026/06/22/b.wav", headers=FUNNEL)
    assert resp.status_code == 404


def test_serve_recording_blocks_traversal(client):
    resp = client.get("/recordings/../config.py", headers=TAILNET)
    assert resp.status_code in (403, 404)
