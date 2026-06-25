from unittest.mock import patch


def test_callback_notifies(client, monkeypatch):
    monkeypatch.setenv("PORT", "8080")
    fake = {
        "RecordingSid": "RE123",
        "RecordingUrl": "https://api.twilio.com/REC",
        "RecordingDuration": "12",
        "From": "+15551112222",
    }
    with patch("app.routes.voicemail.http_requests.get") as get, \
         patch("app.routes.voicemail._delete_from_twilio"), \
         patch("app.routes.voicemail.pushover.send_notification") as notify:
        get.return_value.content = b"RIFFfake"
        get.return_value.raise_for_status.return_value = None
        resp = client.post("/voicemail/callback", data=fake)
    assert resp.status_code == 204
    notify.assert_called_once()


def test_callback_survives_notify_failure(client):
    fake = {
        "RecordingSid": "RE999",
        "RecordingUrl": "https://api.twilio.com/REC9",
        "RecordingDuration": "3",
        "From": "+1",
    }
    with patch("app.routes.voicemail.http_requests.get") as get, \
         patch("app.routes.voicemail._delete_from_twilio"), \
         patch("app.routes.voicemail.pushover.send_notification", side_effect=RuntimeError("x")):
        get.return_value.content = b"RIFFfake"
        get.return_value.raise_for_status.return_value = None
        resp = client.post("/voicemail/callback", data=fake)
    assert resp.status_code == 204


def test_voicemail_threads_caller_into_callback_url(client):
    """The /voicemail TwiML must carry the caller on the recording callback URL,
    because Twilio's recording-status callback does not include From."""
    resp = client.post("/voicemail", data={"From": "+15551112222"})
    body = resp.get_data(as_text=True)
    assert "caller=%2B15551112222" in body


def test_callback_reads_caller_from_query(client):
    """The callback should use the threaded ?caller= value, not 'unknown'."""
    fake = {
        "RecordingSid": "RE777",
        "RecordingUrl": "https://api.twilio.com/REC7",
        "RecordingDuration": "8",
        # note: no 'From' in the form, mirroring Twilio's real callback
    }
    with patch("app.routes.voicemail.http_requests.get") as get, \
         patch("app.routes.voicemail._delete_from_twilio"), \
         patch("app.routes.voicemail.pushover.send_notification") as notify:
        get.return_value.content = b"RIFFfake"
        get.return_value.raise_for_status.return_value = None
        resp = client.post("/voicemail/callback?caller=%2B15559998888", data=fake)
    assert resp.status_code == 204
    sent_message = notify.call_args.kwargs["message"]
    assert "+15559998888" in sent_message
