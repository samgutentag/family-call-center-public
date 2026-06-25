import os
import config
from app.services import voice


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_menu_mentions_weather(client):
    resp = client.post("/call")
    body = resp.get_data(as_text=True)
    assert "Press 1" in body
    assert "weather" in body.lower()


def test_route_digit_1_goes_to_voicemail(client):
    resp = client.post("/call/route", data={"Digits": "1"})
    assert "/voicemail" in resp.get_data(as_text=True)


def test_route_digit_2_goes_to_weather(client):
    resp = client.post("/call/route", data={"Digits": "2"})
    assert "/weather" in resp.get_data(as_text=True)


def test_route_unknown_digit_repeats_menu(client):
    resp = client.post("/call/route", data={"Digits": "9"})
    assert "/call" in resp.get_data(as_text=True)


def test_menu_plays_cached_audio(client):
    os.makedirs(config.Config.AUDIO_DIR, exist_ok=True)
    name = voice.audio_name(voice.MENU_PROMPT)
    with open(os.path.join(config.Config.AUDIO_DIR, name), "wb") as f:
        f.write(b"mp3")  # non-empty: a real cache hit
    resp = client.post("/call")
    body = resp.get_data(as_text=True)
    assert "<Play>" in body
    assert f"/audio/{name}" in body
