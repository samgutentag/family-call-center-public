import os
import tempfile

# Dummy env MUST be set before importing config/app (import-time require_env).
# These are FORCED (not setdefault) so a developer's real .env exported into the
# shell can't pollute the suite: tests stay hermetic and never hit the network
# or the real data dir. Tests that need a real-looking value monkeypatch Config.
os.environ["TWILIO_ACCOUNT_SID"] = "ACtest"
os.environ["TWILIO_AUTH_TOKEN"] = "test-token"
os.environ["TWILIO_PHONE_NUMBER"] = "+15550000000"
os.environ["BASE_URL"] = "https://funnel.example.ts.net"
os.environ["TWILIO_VALIDATION_ENABLED"] = "false"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["TAILNET_HOSTNAME"] = "pi.tailtest.ts.net"
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="ivr-test-")
os.environ["DEEPGRAM_API_KEY"] = ""
os.environ["PUSHOVER_TOKEN"] = ""
os.environ["PUSHOVER_USER"] = ""
os.environ["WEATHER_LAT"] = ""
os.environ["WEATHER_LON"] = ""
os.environ["SPEECH_RATE"] = "1.0"

import pytest
from app import create_app


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()
